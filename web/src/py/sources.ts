// Each project's exact .py files (the ones pytest checks), bundled as text. No copies to drift.
// Globs must be string literals, so each project gets its own line.
type Files = Record<string, string>;
const byName = (files: Files): Files =>
  Object.fromEntries(Object.entries(files).map(([path, text]) => [path.split("/").pop()!, text]));
const opts = { query: "?raw", import: "default", eager: true } as const;

export const aliasSlotsSources = byName(import.meta.glob("../../../projects/01_alias_slots/*.py", opts) as Files);
export const codeTalkSources = byName(import.meta.glob("../../../projects/02_code_talk/*.py", opts) as Files);
export const letterBarsSources = byName(import.meta.glob("../../../projects/03_letter_bars/*.py", opts) as Files);
