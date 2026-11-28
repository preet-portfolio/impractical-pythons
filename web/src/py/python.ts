// A promise-per-request wrapper around the Pyodide worker.

type Pending = { resolve: (value: unknown) => void; reject: (error: Error) => void };

export class Python {
  private worker = new Worker(new URL("./worker.ts", import.meta.url), { type: "module" });
  private seq = 0;
  private pending = new Map<number, Pending>();
  onProgress: (stage: string) => void = () => {};

  constructor() {
    this.worker.onmessage = (event: MessageEvent) => {
      const msg = event.data;
      if (msg.type === "progress") return this.onProgress(msg.stage);
      const waiting = this.pending.get(msg.id);
      if (!waiting) return;
      this.pending.delete(msg.id);
      if (msg.ok) waiting.resolve(msg.result);
      else waiting.reject(new Error(msg.error));
    };
    this.worker.onerror = (event) => {
      for (const waiting of this.pending.values()) waiting.reject(new Error(event.message));
      this.pending.clear();
    };
  }

  private send<T>(message: object): Promise<T> {
    const id = ++this.seq;
    return new Promise<T>((resolve, reject) => {
      this.pending.set(id, { resolve: resolve as (value: unknown) => void, reject });
      this.worker.postMessage({ id, ...message });
    });
  }

  /** Load Pyodide, write a project's .py files and run its bridge (see worker.ts). */
  init(project: string, files: Record<string, string>, bridge: string): Promise<void> {
    return this.send({ type: "init", project, files, bridge });
  }

  call<T>(fn: string, args: object = {}): Promise<T> {
    return this.send({ type: "call", fn, args });
  }
}
