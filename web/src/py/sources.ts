// Each project's exact .py files (the ones pytest checks), bundled as text. No copies to drift.
// Vite needs every glob and its options written out literally, so each project gets its own call.
type Files = Record<string, string>;
const byName = (files: Files): Files =>
  Object.fromEntries(Object.entries(files).map(([path, text]) => [path.split("/").pop()!, text]));

// Shared by several stalls (the word list loader and the "not on the pier" filter).
export const commonSources = byName(
  import.meta.glob("../../../projects/common/*.py", { query: "?raw", import: "default", eager: true }),
);
export const aliasSlotsSources = byName(
  import.meta.glob("../../../projects/01_alias_slots/*.py", { query: "?raw", import: "default", eager: true }),
);
export const codeTalkSources = byName(
  import.meta.glob("../../../projects/02_code_talk/*.py", { query: "?raw", import: "default", eager: true }),
);
export const letterBarsSources = byName(
  import.meta.glob("../../../projects/03_letter_bars/*.py", { query: "?raw", import: "default", eager: true }),
);
export const mirrorSpellsSources = byName(
  import.meta.glob("../../../projects/04_mirror_spells/*.py", { query: "?raw", import: "default", eager: true }),
);
export const shuffleCafeSources = byName(
  import.meta.glob("../../../projects/05_shuffle_cafe/*.py", { query: "?raw", import: "default", eager: true }),
);
