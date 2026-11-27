import "./styles.css";
import { Python } from "./py/python";
import { codeTalkSources } from "./py/sources";

// Python side of the page: called by the worker as _bridge(fn, args_json) -> JSON.
const BRIDGE = `
import json
import code_talk

def _bridge(fn, args_json):
    args = json.loads(args_json)
    text = args.get("text", "")
    if fn == "encode":
        return json.dumps({"text": code_talk.encode(text), "words": code_talk.words_explained(text)})
    if fn == "decode":
        plain = code_talk.decode(text)
        return json.dumps({"text": plain, "words": code_talk.words_explained(plain)})
    raise ValueError(f"Unknown call {fn!r}")
`;

type Explained = { word: string; moves: string; stays: string; result: string; rule: string };
type Translation = { text: string; words: Explained[] };

const SAMPLES = [
  "Meet me by the old fountain at noon.",
  "The quiet squirrel knows where the snacks are hidden.",
  "Yes, the well-known spy can't whistle!",
  "Operation Pancake begins at 0600. Bring syrup.",
];

const $ = <T extends HTMLElement>(id: string) => document.getElementById(id) as T;
const plain = $<HTMLTextAreaElement>("plain");
const coded = $<HTMLTextAreaElement>("coded");
const swap = $<HTMLButtonElement>("swap");
const status = $("status");
const breakdown = $<HTMLOListElement>("breakdown");
const samples = $("samples");

const python = new Python();
let timer = 0;
let request = 0;

/** Translate from whichever box was typed in, after a short pause in typing. */
function schedule(from: "plain" | "coded") {
  window.clearTimeout(timer);
  timer = window.setTimeout(() => void translate(from), 120);
}

async function translate(from: "plain" | "coded") {
  const mine = ++request; // ignore answers to older keystrokes
  const source = from === "plain" ? plain : coded;
  const target = from === "plain" ? coded : plain;
  let result: Translation;
  try {
    result = await python.call<Translation>(from === "plain" ? "encode" : "decode", {
      text: source.value,
    });
  } catch (error) {
    console.error(error);
    status.textContent = "That text couldn't be translated. Try editing it, or reload the page.";
    return;
  }
  if (mine !== request) return;
  target.value = result.text;
  renderBreakdown(result.words);
}

function renderBreakdown(words: Explained[]) {
  breakdown.replaceChildren(
    ...words.map((w) => {
      const li = document.createElement("li");
      const word = document.createElement("span");
      word.className = "bd-word";
      const moves = document.createElement("mark");
      moves.textContent = w.moves;
      word.append(moves, document.createTextNode(w.stays));
      const arrow = document.createElement("span");
      arrow.className = "bd-arrow";
      arrow.setAttribute("aria-label", "becomes");
      arrow.textContent = "→";
      const result = document.createElement("span");
      result.className = "bd-result";
      result.textContent = w.result;
      const rule = document.createElement("span");
      rule.className = "bd-rule";
      rule.textContent = w.rule;
      li.append(word, arrow, result, rule);
      return li;
    }),
  );
}

async function copy(box: HTMLTextAreaElement, label: string) {
  try {
    await navigator.clipboard.writeText(box.value);
    status.textContent = `Copied the ${label}.`;
  } catch {
    box.select();
    status.textContent = "Copying isn't allowed here. The text is selected, so press Ctrl-C or ⌘-C.";
  }
}

async function start() {
  python.onProgress = (stage) => (status.textContent = `${stage}…`);
  try {
    await python.init("code_talk", codeTalkSources, BRIDGE);
  } catch (error) {
    console.error(error);
    status.textContent = "Python couldn't start in this browser. Check your connection and reload the page.";
    return;
  }
  plain.addEventListener("input", () => schedule("plain"));
  coded.addEventListener("input", () => schedule("coded"));
  swap.addEventListener("click", () => {
    [plain.value, coded.value] = [coded.value, plain.value];
    void translate("plain");
    plain.focus();
  });
  document.querySelectorAll<HTMLButtonElement>(".pane-copy").forEach((button) => {
    const box = button.dataset.copy === "plain" ? plain : coded;
    button.addEventListener("click", () => copy(box, button.dataset.copy === "plain" ? "plain text" : "Code-Talk"));
  });
  for (const text of SAMPLES) {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = text;
    button.addEventListener("click", () => {
      plain.value = text;
      void translate("plain");
    });
    samples.append(button);
  }
  plain.disabled = coded.disabled = swap.disabled = false;
  plain.value = SAMPLES[0];
  await translate("plain");
  status.textContent = "Type in either box.";
}

void start();
