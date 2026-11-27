import "./styles.css";
import "./pier-telegraph.css";
import { Python } from "./py/python";
import { pierTelegraphSources } from "./py/sources";

// Python side of the page: called by the worker as _bridge(fn, args_json) -> JSON.
// The page never builds a key or grid itself; it only offers choices Python says are valid.
const BRIDGE = `
import json

import codebook
import route

def alternating(cols):
    """Up the first column, down the next, and so on."""
    return [-(n + 1) if n % 2 == 0 else n + 1 for n in range(cols)]

def usable(key, cols):
    """The visitor's key if it fits this many columns, else None."""
    try:
        return route.check_key(list(key or []), cols)
    except route.KeyProblem:
        return None

def snug(options):
    return min(options, key=lambda o: (o["filler"], abs(o["cols"] - o["rows"]), -o["cols"]))

def send(args):
    text = args["text"]
    words = codebook.encode(text) if args["code"] else codebook.plain_words(text)
    if len(words) < 2:
        return {"empty": True}
    options = codebook.grid_options(len(words))
    option = next((o for o in options if o["cols"] == args.get("cols")), None) or snug(options)
    cols, rows = option["cols"], option["rows"]
    key = usable(args.get("key"), cols) or alternating(cols)
    grid = codebook.pad(words, cols, rows, seed=11)
    order = route.route_order(cols, rows, key)
    return {
        "count": len(words), "options": options, "cols": cols, "rows": rows, "key": key,
        "grid": grid, "order": order, "cipher": [grid[cell] for cell in order],
    }

def puzzle(practice):
    """The telegram on the counter: its original words and how it was sent."""
    if practice:
        t = codebook.TICKETS
        return t["words"], t["cols"], t["rows"], t["key"]
    m = codebook.MYSTERY
    words = codebook.pad(codebook.encode(m["text"]), m["cols"], m["rows"], m["seed"])
    return words, m["cols"], m["rows"], m["key"]

def crack(args):
    original, true_cols, true_rows, true_key = puzzle(args["practice"])
    cipher = route.encrypt(original, true_cols, true_rows, true_key)
    sizes = [{"cols": c, "rows": len(cipher) // c} for c in route.factors(len(cipher))]
    size = next((s for s in sizes if s["cols"] == args.get("cols")), sizes[0])
    cols, rows = size["cols"], size["rows"]
    key = usable(args.get("key"), cols) or list(range(1, cols + 1))
    words = route.decrypt(cipher, cols, rows, key)
    right = sum(a == b for a, b in zip(words, original))
    solved = right == len(original)
    return {
        "cipher": cipher, "sizes": sizes, "cols": cols, "rows": rows, "key": key,
        "words": words, "order": route.route_order(cols, rows, key), "right": right,
        "solved": solved, "meaning": codebook.decode(words) if solved else "",
    }

def _bridge(fn, args_json):
    args = json.loads(args_json)
    if fn == "book":
        return json.dumps({"book": codebook.CODEBOOK, "sample": codebook.SAMPLE})
    if fn == "send":
        return json.dumps(send(args))
    if fn == "crack":
        return json.dumps(crack(args))
    raise ValueError(f"Unknown call {fn!r}")
`;

type Option = { cols: number; rows: number; filler: number };
type Sent = {
  empty?: boolean;
  count: number;
  options: Option[];
  cols: number;
  rows: number;
  key: number[];
  grid: string[];
  order: number[];
  cipher: string[];
};
type Cracked = {
  cipher: string[];
  sizes: { cols: number; rows: number }[];
  cols: number;
  rows: number;
  key: number[];
  words: string[];
  order: number[];
  right: number;
  solved: boolean;
  meaning: string;
};

const $ = <T extends HTMLElement>(id: string) => document.getElementById(id) as T;
const python = new Python();
const calm = () => matchMedia("(prefers-reduced-motion: reduce)").matches;
let codeWords = new Set<string>();

// ---- pieces shared by both counters -------------------------------------------------------

function button(text: string, className: string, onClick: () => void, label?: string) {
  const b = document.createElement("button");
  b.type = "button";
  b.className = className;
  b.textContent = text;
  if (label) b.setAttribute("aria-label", label);
  b.addEventListener("click", onClick);
  return b;
}

/** What kind of word this is, for styling: a code word, filler, or plain. */
function kind(word: string, isFiller: boolean) {
  if (codeWords.has(word)) return "is-code";
  return isFiller ? "is-filler" : "";
}

/** Fill the pigeonholes, row by row, the way the message was written. */
function renderHoles(holes: HTMLOListElement, cols: number, words: string[], filler: (i: number) => boolean) {
  holes.style.setProperty("--cols", String(cols));
  holes.replaceChildren(
    ...words.map((word, i) => {
      const li = document.createElement("li");
      const slip = document.createElement("span");
      slip.className = `slip ${kind(word, filler(i))}`;
      slip.textContent = word;
      li.append(slip);
      return li;
    }),
  );
}

/** Above each column: which step of the route it is, and which way it's read. */
function renderHeads(heads: HTMLElement, cols: number, key: number[]) {
  heads.style.setProperty("--cols", String(cols));
  heads.replaceChildren(
    ...Array.from({ length: cols }, (_, column) => {
      const step = key.findIndex((n) => Math.abs(n) === column + 1);
      const span = document.createElement("span");
      span.textContent = `${step + 1}${key[step] < 0 ? "↑" : "↓"}`;
      return span;
    }),
  );
}

/**
 * Draw the route as a strip of ticker tape running through the pigeonholes in route order.
 * It runs behind the word slips (see .route-line in the CSS), so the words stay readable.
 */
function drawRoute(rack: HTMLElement, svg: SVGSVGElement, holes: HTMLOListElement, order: number[], animate: boolean) {
  const box = rack.getBoundingClientRect();
  const cells = [...holes.children] as HTMLElement[];
  if (!cells.length) return;
  // Each column is one run of `rows` cells. The tape runs down the middle of the column and
  // turns round in the rack's top and bottom margins, so it never crosses a word sideways.
  const cols = Number(holes.style.getPropertyValue("--cols")) || 1;
  const rows = cells.length / cols;
  const top = 4;
  const bottom = box.height - 4;
  const points: number[][] = [];
  for (let run = 0; run < order.length; run += rows) {
    const column = order.slice(run, run + rows).map((cell) => {
      const r = cells[cell].getBoundingClientRect();
      return [r.left - box.left + r.width / 2, r.top - box.top + r.height / 2];
    });
    const goingDown = column.length < 2 || column[0][1] < column[1][1];
    const x = column[0][0];
    points.push([x, goingDown ? top : bottom], ...column, [x, goingDown ? bottom : top]);
  }
  svg.setAttribute("viewBox", `0 0 ${box.width} ${box.height}`);
  const d = points.map(([x, y], i) => `${i ? "L" : "M"}${x.toFixed(1)} ${y.toFixed(1)}`).join(" ");
  const [sx, sy] = points[0];
  svg.innerHTML = `
    <defs><marker id="${svg.id}-head" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
      <path d="M0 0 L10 5 L0 10 z" class="route-arrow" /></marker></defs>
    <path class="route-path" d="${d}" marker-end="url(#${svg.id}-head)" />
    <circle class="route-start" cx="${sx}" cy="${sy}" r="6" />`;
  const path = svg.querySelector<SVGPathElement>(".route-path")!;
  if (animate && !calm()) {
    // Unroll the tape: a dash as long as the path, slid from fully hidden to fully shown.
    const length = path.getTotalLength();
    path.style.strokeDasharray = `${length}`;
    path
      .animate([{ strokeDashoffset: length }, { strokeDashoffset: 0 }], { duration: 900, easing: "ease-in-out" })
      .finished.then(() => path.style.removeProperty("stroke-dasharray"), () => {});
  }
}

function renderTape(tape: HTMLOListElement, words: string[], isFiller: (word: string) => boolean, animate: boolean) {
  tape.replaceChildren(
    ...words.map((word, i) => {
      const li = document.createElement("li");
      li.textContent = word;
      li.className = kind(word, isFiller(word));
      if (animate && !calm()) li.style.animationDelay = `${i * 45}ms`;
      if (animate && !calm()) li.classList.add("is-fed");
      return li;
    }),
  );
}

function renderSizes(box: HTMLElement, sizes: { cols: number; rows: number; filler?: number }[], cols: number, pick: (cols: number) => void) {
  box.replaceChildren(
    ...sizes.map((size) => {
      const filler = size.filler ? `+${size.filler} filler` : "";
      const b = button("", "size-chip", () => pick(size.cols), `${size.cols} columns by ${size.rows} rows${filler ? `, ${filler}` : ""}`);
      const dims = document.createElement("span");
      dims.className = "size-dims";
      dims.textContent = `${size.cols} × ${size.rows}`;
      b.append(dims);
      if (filler) {
        const extra = document.createElement("span");
        extra.className = "size-filler";
        extra.textContent = filler;
        b.append(extra);
      }
      b.setAttribute("aria-pressed", String(size.cols === cols));
      return b;
    }),
  );
}

/**
 * The route builder: one chip per step, in route order. Tapping a chip flips that column's
 * direction; the small arrows swap it with its neighbour. Every key it can make is valid.
 */
function renderRoute(list: HTMLOListElement, keyLine: HTMLElement, key: number[], change: (key: number[]) => void) {
  keyLine.textContent = key.join(" ");
  list.replaceChildren(
    ...key.map((n, i) => {
      const li = document.createElement("li");
      const column = Math.abs(n);
      const flip = button("", "route-chip", () => {
        change(key.map((m, j) => (j === i ? -m : m)));
      }, `Step ${i + 1}: column ${column}, read ${n < 0 ? "upwards" : "downwards"}. Tap to flip.`);
      const word = document.createElement("span");
      word.className = "col-word";
      word.textContent = "Column ";
      flip.append(word, `${column} ${n < 0 ? "↑" : "↓"}`);
      const swap = (j: number) => {
        const next = [...key];
        [next[i], next[j]] = [next[j], next[i]];
        change(next);
      };
      const earlier = button("◀", "nudge", () => swap(i - 1), `Move column ${column} earlier in the route`);
      const later = button("▶", "nudge", () => swap(i + 1), `Move column ${column} later in the route`);
      earlier.disabled = i === 0;
      later.disabled = i === key.length - 1;
      li.append(earlier, flip, later);
      return li;
    }),
  );
}

// ---- Send a telegram ------------------------------------------------------------------------

const message = $<HTMLTextAreaElement>("message");
const useBook = $<HTMLInputElement>("use-book");
const sendStatus = $("send-status");
const sendCopy = $<HTMLButtonElement>("send-copy");
let sent: Sent | null = null;
let sendCols: number | null = null;
let sendKey: number[] | null = null;
let sendRequest = 0;
let sendTimer = 0;

async function send(animate = true) {
  const mine = ++sendRequest;
  try {
    const result = await python.call<Sent>("send", {
      text: message.value,
      code: useBook.checked,
      cols: sendCols,
      key: sendKey,
    });
    if (mine !== sendRequest) return;
    if (result.empty) {
      sendStatus.textContent = "Write a message of at least two words for the clerk.";
      sendCopy.disabled = true;
      return;
    }
    sent = result;
    sendCols = result.cols;
    sendKey = result.key;
    const filler = (i: number) => i >= result.count;
    const fillerWords = new Set(result.grid.slice(result.count));
    renderSizes($("send-sizes"), result.options, result.cols, (cols) => {
      sendCols = cols;
      sendKey = null; // a new rack gets the classic up-and-down route
      void send();
    });
    renderHoles($<HTMLOListElement>("send-holes"), result.cols, result.grid, filler);
    renderHeads($("send-heads"), result.cols, result.key);
    renderRoute($<HTMLOListElement>("send-route"), $("send-key"), result.key, (key) => {
      sendKey = key;
      void send();
    });
    renderTape($<HTMLOListElement>("send-tape"), result.cipher, (w) => fillerWords.has(w), animate);
    requestAnimationFrame(() => drawRoute($("send-rack"), $("send-line") as unknown as SVGSVGElement, $("send-holes") as HTMLOListElement, result.order, animate));
    const pad = result.grid.length - result.count;
    sendStatus.textContent =
      `${result.count} words in a ${result.cols} × ${result.rows} rack` +
      (pad ? `, plus ${pad} filler ${pad === 1 ? "word" : "words"}` : "") +
      `. Send the telegram, and tell the other office the key (${result.cols} columns, ${result.key.join(" ")}) some other way.`;
    sendCopy.disabled = false;
  } catch (error) {
    console.error(error);
    sendStatus.textContent = "The wire's gone quiet. Try that again.";
  }
}

// ---- Crack a telegram -----------------------------------------------------------------------

const practice = $<HTMLInputElement>("practice");
const crackStatus = $("crack-status");
const delivered = $("delivered");
const decoded = $("decoded");
let crackCols: number | null = null;
let crackKey: number[] | null = null;
let crackRequest = 0;
let wasSolved = false;

async function crack(animate = false) {
  const mine = ++crackRequest;
  try {
    const result = await python.call<Cracked>("crack", { practice: practice.checked, cols: crackCols, key: crackKey });
    if (mine !== crackRequest) return;
    crackCols = result.cols;
    crackKey = result.key;
    $("crack-tape-label").textContent = practice.checked ? "Practice tickets" : "Received at 9:14";
    renderTape($<HTMLOListElement>("crack-tape"), result.cipher, () => false, animate);
    renderSizes($("crack-sizes"), result.sizes, result.cols, (cols) => {
      crackCols = cols;
      crackKey = null;
      void crack();
    });
    renderRoute($<HTMLOListElement>("crack-route"), $("crack-key"), result.key, (key) => {
      crackKey = key;
      void crack();
    });
    renderHoles($<HTMLOListElement>("crack-holes"), result.cols, result.words, () => false);
    renderHeads($("crack-heads"), result.cols, result.key);
    requestAnimationFrame(() => drawRoute($("crack-rack"), $("crack-line") as unknown as SVGSVGElement, $("crack-holes") as HTMLOListElement, result.order, false));
    delivered.hidden = !result.solved;
    decoded.hidden = !result.solved || practice.checked;
    if (result.solved) {
      if (!wasSolved && !calm()) delivered.classList.add("is-stamping");
      crackStatus.textContent = practice.checked
        ? "1 to 15, every ticket in order. Now try the real telegram!"
        : "Every word is back in its pigeonhole. Delivered!";
      const sentence = result.meaning.charAt(0).toUpperCase() + result.meaning.slice(1);
      decoded.textContent = `With the code book, it says: “${sentence}.”`;
    } else {
      delivered.classList.remove("is-stamping");
      const total = result.words.length;
      crackStatus.textContent =
        result.right === 0
          ? "Nothing in the right place yet. Try another rack size or route."
          : `${result.right} of ${total} words are in the right pigeonhole.`;
    }
    wasSolved = result.solved;
  } catch (error) {
    console.error(error);
    crackStatus.textContent = "The tape snapped. Try that again.";
  }
}

// ---- opening up -----------------------------------------------------------------------------

async function start() {
  python.onProgress = (stage) => (sendStatus.textContent = `${stage}…`);
  try {
    await python.init("pier_telegraph", pierTelegraphSources, BRIDGE);
    const { book, sample } = await python.call<{ book: Record<string, string>; sample: string }>("book", {});
    codeWords = new Set(Object.keys(book));
    $("code-list").replaceChildren(
      ...Object.entries(book).flatMap(([code, meaning]) => {
        const dt = document.createElement("dt");
        dt.textContent = code;
        const dd = document.createElement("dd");
        dd.textContent = meaning;
        return [dt, dd];
      }),
    );
    message.value = sample;
  } catch (error) {
    console.error(error);
    sendStatus.textContent = "The office couldn't open. Check your connection and reload the page.";
    return;
  }
  message.disabled = useBook.disabled = practice.disabled = false;
  message.addEventListener("input", () => {
    window.clearTimeout(sendTimer);
    sendTimer = window.setTimeout(() => {
      sendCols = null; // a new message picks its own snug rack
      sendKey = null;
      void send(false);
    }, 250);
  });
  useBook.addEventListener("change", () => {
    sendCols = null;
    sendKey = null;
    void send();
  });
  practice.addEventListener("change", () => {
    crackCols = null;
    crackKey = null;
    wasSolved = false;
    void crack(true);
  });
  sendCopy.addEventListener("click", async () => {
    if (!sent) return;
    try {
      await navigator.clipboard.writeText(sent.cipher.join(" "));
      sendStatus.textContent = `Copied. The key is ${sent.cols} columns, ${sent.key.join(" ")}: send that separately!`;
    } catch {
      sendStatus.textContent = `Copy this: ${sent.cipher.join(" ")}`;
    }
  });
  // Redraw the route lines when the racks change size (a phone turning, a window resizing).
  const redraw = new ResizeObserver(() => {
    if (sent) drawRoute($("send-rack"), $("send-line") as unknown as SVGSVGElement, $("send-holes") as HTMLOListElement, sent.order, false);
  });
  redraw.observe($("send-rack"));
  await send();
  await crack(true);
}

void start();
