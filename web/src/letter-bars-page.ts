import "./styles.css";
import "./letter-bars.css";
import { Python } from "./py/python";
import { letterBarsSources } from "./py/sources";

// Python side of the page: called by the worker as _bridge(fn, args_json) -> JSON.
const BRIDGE = `
import json
import letter_bars

def _bridge(fn, args_json):
    args = json.loads(args_json)
    if fn == "samples":
        return json.dumps(letter_bars.SAMPLES)
    if fn == "chart":
        return json.dumps(letter_bars.chart_data(args["a"], args.get("b")))
    raise ValueError(f"Unknown call {fn!r}")
`;

type Summary = {
  total: number;
  counts: Record<string, number>;
  shares: Record<string, number>;
  top: string;
  accents: Record<string, number>;
};
type Chart = {
  letters: string[];
  english: Record<string, number>;
  english_top: string;
  a: Summary;
  b: Summary | null;
};

const $ = <T extends HTMLElement>(id: string) => document.getElementById(id) as T;
const textA = $<HTMLTextAreaElement>("text-a");
const textB = $<HTMLTextAreaElement>("text-b");
const paneB = $("pane-b");
const keyB = $("key-b");
const compareBox = $<HTMLInputElement>("compare");
const usedOnly = $<HTMLInputElement>("used-only");
const status = $("status");
const chart = $<HTMLOListElement>("chart");
const summary = $("summary");

const python = new Python();
let timer = 0;
let request = 0;

function schedule() {
  window.clearTimeout(timer);
  timer = window.setTimeout(() => void redraw(), 120);
}

async function redraw() {
  const mine = ++request; // ignore answers to older keystrokes
  let data: Chart;
  try {
    data = await python.call<Chart>("chart", {
      a: textA.value,
      b: compareBox.checked ? textB.value : null,
    });
  } catch (error) {
    console.error(error);
    status.textContent = "That batch stuck to the pan. Try editing the text, or reload the page.";
    return;
  }
  if (mine !== request) return;
  render(data);
}

const pct = (share: number) => (share >= 10 ? share.toFixed(0) : share.toFixed(1)) + "%";

function el<K extends keyof HTMLElementTagNameMap>(tag: K, className: string, text = "") {
  const node = document.createElement(tag);
  node.className = className;
  if (text) node.textContent = text;
  return node;
}

function render(data: Chart) {
  const { a, b, english } = data;
  const letters = usedOnly.checked
    ? data.letters.filter((l) => a.counts[l] || (b && b.counts[l]))
    : data.letters;
  // One scale for every stick and notch, so lengths compare honestly. 14% fits a typical E.
  const top = Math.max(14, ...letters.map((l) => Math.max(a.shares[l], b?.shares[l] ?? 0)));
  const width = (share: number) => `${(100 * share) / top}%`;

  const stick = (share: number, extra: string) => {
    const node = el("span", `stick ${extra}${share ? "" : " is-zero"}`);
    node.style.width = width(share);
    return node;
  };

  chart.replaceChildren(
    ...letters.map((letter) => {
      const li = el("li", "stick-row");
      const end = el("span", "rock-end", letter.toUpperCase());
      const track = el("span", "stick-track");
      track.append(stick(a.shares[letter], "stick-a"));
      if (b) track.append(stick(b.shares[letter], "stick-b"));
      const usual = el("span", "usual");
      usual.style.left = width(english[letter]);
      track.append(usual);
      const value = el(
        "span",
        "stick-value",
        b ? `${pct(a.shares[letter])} / ${pct(b.shares[letter])}` : pct(a.shares[letter]),
      );

      // Screen readers get one plain sentence instead of loose shapes and numbers.
      li.setAttribute(
        "aria-label",
        `${letter.toUpperCase()}: ${pct(a.shares[letter])}` +
          (b ? `, second text ${pct(b.shares[letter])}` : "") +
          `, usual English ${pct(english[letter])}`,
      );
      for (const part of [end, track, value]) part.setAttribute("aria-hidden", "true");
      li.append(end, track, value);
      return li;
    }),
  );
  if (!letters.length) chart.append(el("li", "sticks-empty", "The jar's empty. Type something above."));

  summary.replaceChildren(
    receiptLine("Your favourite letters", a, ""),
    ...(b ? [receiptLine("The second text's favourites", b, "is-b")] : []),
    receiptLine("Usual English", null, "", data.english_top),
  );
}

function receiptLine(name: string, s: Summary | null, className: string, top = "") {
  const line = el("p", className);
  line.style.margin = "0";
  if (s && !s.total) {
    line.textContent = `${name}: nothing yet`;
    return line;
  }
  const letters = (s ? s.top : top).toUpperCase().split("").join(" ");
  line.append(`${name}: `, el("strong", "", letters));
  if (s) {
    const accents = Object.entries(s.accents)
      .map(([char, n]) => `${char} ×${n}`)
      .join(", ");
    line.append(` from ${s.total} ${s.total === 1 ? "letter" : "letters"}`);
    if (accents) line.append(`. Accents folded in: ${accents}`);
  }
  return line;
}

function fillSampleButtons(samples: Record<string, string>) {
  document.querySelectorAll<HTMLElement>(".flavours").forEach((row) => {
    const box = row.dataset.for === "b" ? textB : textA;
    for (const [language, text] of Object.entries(samples)) {
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = `${language} postcard`;
      button.addEventListener("click", () => {
        box.value = text;
        void redraw();
      });
      row.append(button);
    }
  });
}

async function start() {
  python.onProgress = (stage) => (status.textContent = `${stage}…`);
  let samples: Record<string, string>;
  try {
    await python.init("letter_bars", letterBarsSources, BRIDGE);
    samples = await python.call<Record<string, string>>("samples");
  } catch (error) {
    console.error(error);
    status.textContent = "Python couldn't start in this browser. Check your connection and reload the page.";
    return;
  }
  fillSampleButtons(samples);
  textA.addEventListener("input", schedule);
  textB.addEventListener("input", schedule);
  usedOnly.addEventListener("change", () => void redraw());
  compareBox.addEventListener("change", () => {
    paneB.hidden = keyB.hidden = !compareBox.checked;
    if (compareBox.checked && !textB.value) textB.value = samples.Spanish;
    void redraw();
  });
  textA.disabled = textB.disabled = compareBox.disabled = usedOnly.disabled = false;
  textA.value = samples.English;
  await redraw();
  status.textContent = "Type, paste, or pick a postcard. The rock updates as you go.";
}

void start();
