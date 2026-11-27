/// <reference lib="webworker" />
// Runs CPython (Pyodide) off the main thread so the page never stutters.
// One worker serves one project page.
// Messages in:  { id, type: "init", project, files, bridge } | { id, type: "call", fn, args }
// Messages out: { id, ok: true, result } | { id, ok: false, error } | { type: "progress", stage }
//
// `bridge` is a little Python source that defines `_bridge(fn, args_json) -> str` and returns
// JSON, so no Python objects (and no proxies to forget to destroy) ever cross into JavaScript.

export const PYODIDE_VERSION = "314.0.8";
const INDEX_URL = `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/`;

type PyodideAPI = {
  FS: { mkdirTree(path: string): void; writeFile(path: string, text: string): void };
  runPython(code: string): unknown;
  globals: { get(name: string): (...args: unknown[]) => string };
};

let py: PyodideAPI | null = null;
let bridge: ((...args: unknown[]) => string) | null = null;

const post = (msg: unknown) => (self as unknown as DedicatedWorkerGlobalScope).postMessage(msg);

async function init(project: string, files: Record<string, string>, bridgeSource: string) {
  if (bridge) return;
  post({ type: "progress", stage: "Downloading Python" });
  const { loadPyodide } = await import(/* @vite-ignore */ `${INDEX_URL}pyodide.mjs`);
  py = (await loadPyodide({ indexURL: INDEX_URL })) as PyodideAPI;
  post({ type: "progress", stage: "Loading the project" });
  const dir = `/home/pyodide/${project}`;
  py.FS.mkdirTree(dir);
  for (const [name, text] of Object.entries(files)) py.FS.writeFile(`${dir}/${name}`, text);
  py.runPython(`import sys\nsys.path.insert(0, ${JSON.stringify(dir)})`);
  py.runPython(bridgeSource);
  bridge = py.globals.get("_bridge");
}

self.onmessage = async (event: MessageEvent) => {
  const { id, type } = event.data;
  try {
    if (type === "init") {
      await init(event.data.project, event.data.files, event.data.bridge);
      post({ id, ok: true, result: null });
    } else if (type === "call") {
      if (!bridge) throw new Error("Python isn't ready yet.");
      const raw = bridge(event.data.fn, JSON.stringify(event.data.args ?? {}));
      post({ id, ok: true, result: JSON.parse(raw) });
    }
  } catch (error) {
    post({ id, ok: false, error: error instanceof Error ? error.message : String(error) });
  }
};
