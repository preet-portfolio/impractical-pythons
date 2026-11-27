/// <reference lib="webworker" />
// Runs CPython (Pyodide) off the main thread so the reels never stutter.
// Messages in:  { id, type: "init", files } | { id, type: "call", fn, args }
// Messages out: { id, ok: true, result } | { id, ok: false, error } | { type: "progress", stage }

export const PYODIDE_VERSION = "314.0.8";
const INDEX_URL = `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/`;
const PROJECT_DIR = "/home/pyodide/project";

type PyodideAPI = {
  FS: { mkdirTree(path: string): void; writeFile(path: string, text: string): void };
  runPython(code: string): unknown;
  globals: { get(name: string): (...args: unknown[]) => string };
};

let py: PyodideAPI | null = null;
let bridge: ((...args: unknown[]) => string) | null = null;

// Calls go through one Python function that returns JSON, so no Python objects
// (and no proxies to forget to destroy) ever cross into JavaScript.
const BRIDGE = `
import json, sys
from dataclasses import asdict
sys.path.insert(0, "${PROJECT_DIR}")
import slots

def _bridge(fn, args_json):
    args = json.loads(args_json)
    if fn == "catalogue":
        return json.dumps(slots.catalogue())
    if fn == "spin":
        locked = {int(k): v for k, v in args["locked"].items()}
        return json.dumps(asdict(slots.spin(args["theme"], None, locked)))
    if fn == "decode":
        try:
            return json.dumps(asdict(slots.decode(args["code"])))
        except ValueError as error:
            return json.dumps({"error": str(error)})
    if fn == "version":
        return sys.version.split()[0]
    raise ValueError(f"Unknown call {fn!r}")
`;

const post = (msg: unknown) => (self as unknown as DedicatedWorkerGlobalScope).postMessage(msg);

async function init(files: Record<string, string>) {
  if (py) return;
  post({ type: "progress", stage: "Downloading Python" });
  const { loadPyodide } = await import(/* @vite-ignore */ `${INDEX_URL}pyodide.mjs`);
  py = (await loadPyodide({ indexURL: INDEX_URL })) as PyodideAPI;
  post({ type: "progress", stage: "Loading the reels" });
  py.FS.mkdirTree(PROJECT_DIR);
  for (const [name, text] of Object.entries(files)) py.FS.writeFile(`${PROJECT_DIR}/${name}`, text);
  py.runPython(BRIDGE);
  bridge = py.globals.get("_bridge");
}

self.onmessage = async (event: MessageEvent) => {
  const { id, type } = event.data;
  try {
    if (type === "init") {
      await init(event.data.files);
      post({ id, ok: true, result: null });
    } else if (type === "call") {
      if (!bridge) throw new Error("Python isn't ready yet.");
      const raw = bridge(event.data.fn, JSON.stringify(event.data.args ?? {}));
      post({ id, ok: true, result: event.data.fn === "version" ? raw : JSON.parse(raw) });
    }
  } catch (error) {
    post({ id, ok: false, error: error instanceof Error ? error.message : String(error) });
  }
};
