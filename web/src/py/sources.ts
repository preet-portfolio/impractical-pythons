// The exact .py files that pytest checks, bundled as text. No copies to drift out of date.
const files = import.meta.glob("../../../projects/01_alias_slots/*.py", {
  query: "?raw",
  import: "default",
  eager: true,
}) as Record<string, string>;

/** `{ "slots.py": "...source..." }` for the Alias Slots project. */
export const aliasSlotsSources: Record<string, string> = Object.fromEntries(
  Object.entries(files).map(([path, text]) => [path.split("/").pop()!, text]),
);
