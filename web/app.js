"use strict";

const PYODIDE_URL = "https://cdn.jsdelivr.net/pyodide/v0.26.4/full/";
const EXEMPLO_INICIAL = "exemplos/validos/promocao_outubro.vitrine";

const el = {
  codigo: document.getElementById("codigo"),
  resultado: document.getElementById("resultado"),
  status: document.getElementById("status"),
  exemplos: document.getElementById("exemplos"),
  compartilhar: document.getElementById("compartilhar"),
  cursor: document.getElementById("cursor"),
  abas: document.querySelectorAll(".abas button"),
};

let modo = "recibo";
let rodarPython = null;
let ultimoErro = null;
let marcas = [];
let espera = null;

CodeMirror.defineSimpleMode("vitrine", {
  start: [
    { regex: /#.*/, token: "comment" },
    { regex: /R\$\s*(?:\d{1,3}(?:\.\d{3})+|\d+),\d\d/, token: "string" },
    { regex: /\d+%?/, token: "number" },
    { regex: /(?:produto|regra|quando|entao|carrinho|calcular|desconto|frete|em|qtd|total|x)\b/, token: "keyword" },
    { regex: /[a-z_][a-z0-9_]*/, token: "variable" },
    { regex: />=|<=|==|[<>+\-*/=]/, token: "operator" },
  ],
});

const editor = CodeMirror.fromTextArea(el.codigo, {
  mode: "vitrine",
  lineNumbers: true,
  indentUnit: 4,
  tabSize: 4,
  indentWithTabs: false,
  extraKeys: { Tab: (cm) => cm.replaceSelection("    ") },
});

editor.on("change", () => {
  clearTimeout(espera);
  espera = setTimeout(compilar, 250);
});
editor.on("cursorActivity", () => {
  const c = editor.getCursor();
  el.cursor.textContent = `${c.line + 1}:${c.ch + 1}`;
});

function limparMarcas() {
  marcas.forEach((m) => m.clear());
  marcas = [];
  for (let i = 0; i < editor.lineCount(); i++) editor.removeLineClass(i, "background", "linha-erro");
}

function marcarErro(linha, coluna) {
  if (linha < 1 || linha > editor.lineCount()) return;
  const l = linha - 1;
  const texto = editor.getLine(l);
  const inicio = Math.min(coluna - 1, texto.length);
  const palavra = /^[\wR$%.,]+/.exec(texto.slice(inicio));
  const fim = inicio + Math.max(1, palavra ? palavra[0].length : 1);
  editor.addLineClass(l, "background", "linha-erro");
  marcas.push(editor.markText({ line: l, ch: inicio }, { line: l, ch: fim }, { className: "marca-erro" }));
}

function compilar() {
  if (!rodarPython) return;
  limparMarcas();
  const r = JSON.parse(rodarPython(editor.getValue(), modo));
  el.resultado.textContent = r.saida;
  el.resultado.classList.toggle("com-erro", !r.ok);
  if (r.ok) {
    ultimoErro = null;
    el.status.className = "status ok";
    el.status.textContent = "✓ programa aceito";
  } else {
    ultimoErro = r;
    marcarErro(r.linha, r.coluna);
    el.status.className = "status erro";
    el.status.textContent = `✗ erro ${r.fase} na linha ${r.linha}, coluna ${r.coluna} (clique para ir)`;
  }
}

el.status.addEventListener("click", () => {
  if (!ultimoErro || ultimoErro.linha < 1) return;
  editor.focus();
  editor.setCursor({ line: ultimoErro.linha - 1, ch: ultimoErro.coluna - 1 });
});

el.abas.forEach((aba) =>
  aba.addEventListener("click", () => {
    el.abas.forEach((a) => a.setAttribute("aria-selected", String(a === aba)));
    modo = aba.dataset.modo;
    compilar();
  })
);

// o programa vai no #hash da URL em base64url (sem "+" e "/", que a URL altera)
function codificar(texto) {
  const b64 = btoa(String.fromCharCode(...new TextEncoder().encode(texto)));
  return b64.replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}
function decodificar(b64url) {
  const b64 = b64url.replace(/-/g, "+").replace(/_/g, "/");
  return new TextDecoder("utf-8", { fatal: true })
    .decode(Uint8Array.from(atob(b64), (c) => c.charCodeAt(0)));
}

el.compartilhar.addEventListener("click", async () => {
  const url = `${location.origin}${location.pathname}#c=${codificar(editor.getValue())}`;
  history.replaceState(null, "", url);
  try {
    await navigator.clipboard.writeText(url);
    el.compartilhar.textContent = "link copiado";
  } catch {
    el.compartilhar.textContent = "link na barra de endereço";
  }
  setTimeout(() => (el.compartilhar.textContent = "copiar link"), 2000);
});

async function texto(caminho) {
  const resp = await fetch(caminho);
  if (!resp.ok) throw new Error(`não consegui baixar ${caminho}`);
  return resp.text();
}

async function carregarExemplos(manifesto) {
  const rotulo = { validos: "válidos", invalidos: "recusados" };
  for (const grupo of ["validos", "invalidos"]) {
    const og = document.createElement("optgroup");
    og.label = rotulo[grupo];
    for (const ex of manifesto.exemplos.filter((e) => e.grupo === grupo)) {
      const op = new Option(ex.nome, ex.caminho);
      og.append(op);
    }
    el.exemplos.append(og);
  }
  el.exemplos.addEventListener("change", async () => {
    editor.setValue(await texto(el.exemplos.value));
    history.replaceState(null, "", location.pathname);
  });

  const hash = location.hash.startsWith("#c=") ? location.hash.slice(3) : null;
  if (hash) {
    try {
      editor.setValue(decodificar(hash));
      el.exemplos.selectedIndex = -1;
      return;
    } catch {
      /* link inválido: cai no exemplo padrão */
    }
  }
  el.exemplos.value = EXEMPLO_INICIAL;
  editor.setValue(await texto(EXEMPLO_INICIAL));
}

async function iniciar() {
  const manifesto = JSON.parse(await texto("manifest.json"));
  await carregarExemplos(manifesto);

  const py = await loadPyodide({ indexURL: PYODIDE_URL });
  el.status.textContent = "instalando o Lark…";
  await py.loadPackage("micropip");
  await py.pyimport("micropip").install("lark==1.3.1");

  el.status.textContent = "carregando o compilador…";
  py.FS.mkdirTree("/home/pyodide/vitrine");
  for (const nome of manifesto.pacote) {
    py.FS.writeFile(`/home/pyodide/vitrine/${nome}`, await texto(`vitrine/${nome}`));
  }
  py.FS.writeFile("/home/pyodide/ponte.py", await texto("ponte.py"));
  py.runPython("import sys; sys.path.insert(0, '/home/pyodide')");
  rodarPython = py.pyimport("ponte").rodar;
  compilar();
}

iniciar().catch((e) => {
  el.status.className = "status erro";
  el.status.textContent = `não foi possível carregar: ${e.message}`;
});
