import { resolve } from "node:path";
import { defineConfig } from "vite";

// The site imports Python source straight from ../projects (see src/py/sources.ts),
// so Vite must be allowed to read the repo root, not just web/.
export default defineConfig({
  server: { fs: { allow: [resolve(import.meta.dirname, "..")] } },
  worker: { format: "es" },
  build: {
    target: "es2022",
    rollupOptions: {
      input: {
        home: resolve(import.meta.dirname, "index.html"),
        aliasSlots: resolve(import.meta.dirname, "alias-slots/index.html"),
        codeTalk: resolve(import.meta.dirname, "code-talk/index.html"),
        letterBars: resolve(import.meta.dirname, "letter-bars/index.html"),
        mirrorSpells: resolve(import.meta.dirname, "mirror-spells/index.html"),
        shuffleCafe: resolve(import.meta.dirname, "shuffle-cafe/index.html"),
      },
    },
  },
});
