import "./styles.css";
import "./pier-telegraph.css";
import { Python } from "./py/python";
import { pierTelegraphSources } from "./py/sources";

// Python side of the page: called by the worker as _bridge(fn, args_json) -> JSON.
// The page never builds a key, a grid or a challenge link itself; it only offers choices
// Python says are valid, and asks Python whether a crack is right.
const BRIDGE = `
import json
from datetime import date

import challenge
import codebook
import dispatches
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

def send(args):
    text = args["text"]
    words = codebook.encode(text) if args["code"] else codebook.plain_words(text)
    if len(words) < 3:  # two words fit no rack that would hide anything
        return {"empty": True}
    options = codebook.grid_options(len(words), widest=args.get("widest", 8))
    if not options:  # too long for a narrow rack: let it be as wide as it needs
        options = codebook.grid_options(len(words))
    chosen = next((o for o in options if o["cols"] == args.get("cols")), None)
    option = chosen or codebook.snuggest(options)
    cols, rows = option["cols"], option["rows"]
    key = usable(args.get("key"), cols) or alternating(cols)
    grid = codebook.pad(words, cols, rows, seed=11)
    order = route.route_order(cols, rows, key)
    return {
        "count": len(words), "options": options, "cols": cols, "rows": rows, "key": key,
        "grid": grid, "order": order, "cipher": [grid[cell] for cell in order],
        "token": challenge.make_challenge(grid, cols, rows, key),
    }

def puzzle(args):
    """The telegram on the counter: its scrambled words, and how to tell it's cracked."""
    source = args["source"]
    if source == "practice":
        t = codebook.TICKETS
        return {"cipher": route.encrypt(t["words"], t["cols"], t["rows"], t["key"]),
                "answer": t["words"]}
    if source == "challenge":
        sent = challenge.read_challenge(args["token"])
        return {"cipher": sent["cipher"], "fingerprint": sent["fingerprint"]}
    today = dispatches.todays_dispatch(date.fromisoformat(args["today"]))
    cipher = route.encrypt(today["words"], today["cols"], today["rows"], today["key"])
    return {"cipher": cipher, "answer": today["words"], "number": today["number"]}

def crack(args):
    try:
        found = puzzle(args)
    except challenge.ChallengeProblem as problem:
        return {"problem": str(problem)}
    cipher = found["cipher"]
    sizes = [{"cols": c, "rows": len(cipher) // c} for c in route.factors(len(cipher))]
    size = next((s for s in sizes if s["cols"] == args.get("cols")), sizes[0])
    cols, rows = size["cols"], size["rows"]
    key = usable(args.get("key"), cols) or list(range(1, cols + 1))
    words = route.decrypt(cipher, cols, rows, key)
    result = {
        "cipher": cipher, "sizes": sizes, "cols": cols, "rows": rows, "key": key,
        "words": words, "order": route.route_order(cols, rows, key),
        "number": found.get("number"),
    }
    if args.get("check"):
        if "answer" in found:  # we know the answer, so we can say how close they are
            right = sum(a == b for a, b in zip(words, found["answer"]))
            solved = right == len(words)
        else:  # a friend's telegram: only its fingerprint came in the link
            right = None
            solved = challenge.is_solved(words, found["fingerprint"])
        result.update(checked=True, right=right, solved=solved,
                      meaning=codebook.decode(words) if solved else "")
    return result

def _bridge(fn, args_json):
    args = json.loads(args_json)
    if fn == "book":
        return json.dumps({"book": codebook.CODEBOOK, "sample": codebook.SAMPLE,
                           "messages": dispatches.DISPATCHES})
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
  token: string;
};
type Cracked = {
  problem?: string;
  cipher: string[];
  sizes: { cols: number; rows: number }[];
  cols: number;
  rows: number;
  key: number[];
  words: string[];
  order: number[];
  number: number | null;
  checked?: boolean;
  right?: number | null;
  solved?: boolean;
  meaning?: string;
};
type Source = "today" | "practice" | "challenge";

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
      slip.style.setProperty("--chars", String(word.length));
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
  let loops = 0;
  for (let run = 0; run < order.length; run += rows) {
    const column = order.slice(run, run + rows).map((cell) => {
      const r = cells[cell].getBoundingClientRect();
      return [r.left - box.left + r.width / 2, r.top - box.top + r.height / 2];
    });
    const goingDown = column.length < 2 || column[0][1] < column[1][1];
    const x = column[0][0];
    const entry = goingDown ? top : bottom;
    const last = points[points.length - 1];
    if (last && last[1] !== entry) {
      // The last column ended at the other edge: loop the tape round the outside of the rack
      // (out past the edge, along the nearer side, back in) rather than across the words.
      // Each loop runs a little further out than the last, so two loops never share a lane.
      const gap = Math.min(9 + 6 * loops++, 24);
      const outFrom = last[1] === bottom ? box.height + gap : -gap;
      const outTo = entry === top ? -gap : box.height + gap;
      const side = (last[0] + x) / 2 < box.width / 2 ? -gap : box.width + gap;
      points.push([last[0], outFrom], [side, outFrom], [side, outTo], [x, outTo]);
    }
    points.push([x, entry], ...column, [x, goingDown ? bottom : top]);
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
const another = $<HTMLButtonElement>("send-another");
const sendStatus = $("send-status");
const sendLink = $<HTMLButtonElement>("send-link");
const sendCopy = $<HTMLButtonElement>("send-copy");
let sent: Sent | null = null;
let sendCols: number | null = null;
let sendKey: number[] | null = null;
let sendRequest = 0;
let sendTimer = 0;
let messages: string[] = [];

const challengeUrl = (token: string) => `${location.origin}${location.pathname}#crack=${token}`;

async function send(animate = true) {
  const mine = ++sendRequest;
  try {
    const result = await python.call<Sent>("send", {
      widest: matchMedia("(max-width: 30rem)").matches ? 5 : 8, // eight columns won't fit a phone
      text: message.value,
      code: useBook.checked,
      cols: sendCols,
      key: sendKey,
    });
    if (mine !== sendRequest) return;
    if (result.empty) {
      sendStatus.textContent = "Write a message of at least three words for the clerk.";
      sendLink.disabled = sendCopy.disabled = true;
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
      ". Send it as a challenge: your friend gets the scrambled telegram and has to crack the route.";
    sendLink.disabled = sendCopy.disabled = false;
  } catch (error) {
    console.error(error);
    sendStatus.textContent = "The wire's gone quiet. Try that again.";
  }
}

/** Copy text, or show it to copy by hand if the browser says no. */
async function copy(text: string, done: string, status: HTMLElement) {
  try {
    await navigator.clipboard.writeText(text);
    status.textContent = done;
  } catch {
    status.textContent = `Copy this: ${text}`;
  }
}

// ---- Crack a telegram -----------------------------------------------------------------------

const practice = $<HTMLInputElement>("practice");
const crackLede = $("crack-lede");
const crackStatus = $("crack-status");
const checkButton = $<HTMLButtonElement>("crack-check");
const delivered = $("delivered");
const decoded = $("decoded");
const afterCrack = $("after-crack");
const shareResult = $<HTMLButtonElement>("share-result");
const reply = $<HTMLButtonElement>("reply");
const TODAY_LEDE =
  "Today's telegram came in this morning, and nobody wrote down the route. Choose the size of the rack, rearrange the columns until the words read as a sentence, then check the route.";
const CHALLENGE_LEDE =
  "Someone sent you this telegram, scrambled. Choose the size of the rack, rearrange the columns until it reads as a sentence, then check the route.";
let crackCols: number | null = null;
let crackKey: number[] | null = null;
let crackRequest = 0;
let checks = 0;
let token = ""; // a friend's challenge, from the link
let number: number | null = null;

const source = (): Source => (practice.checked ? "practice" : token ? "challenge" : "today");
const today = () => new Date().toLocaleDateString("en-CA"); // the visitor's own date, as 2026-11-28
const plural = (n: number, word: string) => `${n} ${word}${n === 1 ? "" : "s"}`;

/** Put the counter back to a fresh telegram: no checks used, no stamp. */
function resetCrack() {
  crackCols = null;
  crackKey = null;
  checks = 0;
  showSolved(false);
}

function showSolved(solved: boolean) {
  delivered.hidden = !solved;
  decoded.hidden = !solved || source() === "practice";
  afterCrack.hidden = !solved;
  if (!solved) delivered.classList.remove("is-stamping");
}

async function crack(animate = false, check = false) {
  const mine = ++crackRequest;
  try {
    const result = await python.call<Cracked>("crack", {
      source: source(),
      today: today(),
      token,
      cols: crackCols,
      key: crackKey,
      check,
    });
    if (mine !== crackRequest) return;
    if (result.problem) {
      // A smudged link: say so, and put today's telegram on the counter instead.
      token = "";
      history.replaceState(null, "", location.pathname);
      crackLede.textContent = TODAY_LEDE;
      await crack(true);
      crackStatus.textContent = `${result.problem} Here's today's telegram instead.`;
      return;
    }
    crackCols = result.cols;
    crackKey = result.key;
    number = result.number;
    const where = source();
    $("crack-tape-label").textContent =
      where === "practice" ? "Practice tickets" : where === "challenge" ? "A telegram for you" : `Telegram No. ${result.number}, on the counter today`;
    renderTape($<HTMLOListElement>("crack-tape"), result.cipher, () => false, animate);
    renderSizes($("crack-sizes"), result.sizes, result.cols, (cols) => {
      crackCols = cols;
      crackKey = null;
      changed();
    });
    renderRoute($<HTMLOListElement>("crack-route"), $("crack-key"), result.key, (key) => {
      crackKey = key;
      changed();
    });
    renderHoles($<HTMLOListElement>("crack-holes"), result.cols, result.words, () => false);
    renderHeads($("crack-heads"), result.cols, result.key);
    requestAnimationFrame(() => drawRoute($("crack-rack"), $("crack-line") as unknown as SVGSVGElement, $("crack-holes") as HTMLOListElement, result.order, false));
    if (result.checked) report(result);
  } catch (error) {
    console.error(error);
    crackStatus.textContent = "The tape snapped. Try that again.";
  }
}

/** The visitor moved something: any stamp comes off until they check again. */
function changed() {
  const wasSolved = !delivered.hidden;
  showSolved(false);
  crackStatus.textContent = wasSolved
    ? "You've moved the rack since it was delivered. Check the route again when it reads right."
    : "When the rack reads as a sentence, check the route.";
  void crack();
}

function report(result: Cracked) {
  const where = source();
  if (result.solved) {
    showSolved(true);
    if (!calm()) {
      delivered.classList.remove("is-stamping");
      void delivered.offsetWidth; // restart the stamp animation
      delivered.classList.add("is-stamping");
    }
    crackStatus.textContent =
      where === "practice"
        ? `1 to 15, every ticket in order, on check ${checks}. Now try today's telegram!`
        : `Every word is back in its pigeonhole. Delivered on check ${checks}!`;
    const sentence = (result.meaning ?? "").charAt(0).toUpperCase() + (result.meaning ?? "").slice(1);
    decoded.textContent = `With the code book, it says: “${sentence}.”`;
    shareResult.hidden = where === "practice";
    reply.textContent = where === "challenge" ? "Send a reply telegram" : "Send your own telegram";
    return;
  }
  const total = result.words.length;
  crackStatus.textContent =
    result.right === null || result.right === undefined
      ? `Check ${checks}: not yet. The words aren't in the sender's order.`
      : `Check ${checks}: ${result.right} of the ${total} words ${result.right === 1 ? "is" : "are"} in the right pigeonhole.`;
}

/** Open a friend's telegram from a link like /pier-telegraph/#crack=eyJ0Ijpb... */
function readLink() {
  const match = /^#crack=([A-Za-z0-9_-]+)$/.exec(location.hash);
  if (!match) return false;
  token = match[1];
  practice.checked = false;
  crackLede.textContent = CHALLENGE_LEDE;
  crackStatus.textContent = "When the rack reads as a sentence, check the route.";
  return true;
}

// ---- opening up -----------------------------------------------------------------------------

// The first visit downloads Python, which takes a few seconds: say so, in the office's voice.
const STAGES: Record<string, string> = {
  "Downloading Python": "Stringing the telegraph wire. The first visit takes a few seconds…",
  "Loading the project": "Testing the line…",
};

async function start() {
  python.onProgress = (stage) => {
    sendStatus.textContent = crackStatus.textContent = STAGES[stage] ?? `${stage}…`;
  };
  try {
    await python.init("pier_telegraph", pierTelegraphSources, BRIDGE);
    const book = await python.call<{ book: Record<string, string>; sample: string; messages: string[] }>("book", {});
    codeWords = new Set(Object.keys(book.book));
    messages = book.messages;
    $("code-list").replaceChildren(
      ...Object.entries(book.book).flatMap(([code, meaning]) => {
        const dt = document.createElement("dt");
        dt.textContent = code;
        const dd = document.createElement("dd");
        dd.textContent = meaning;
        return [dt, dd];
      }),
    );
    message.value = book.sample;
  } catch (error) {
    console.error(error);
    sendStatus.textContent = crackStatus.textContent = "The office couldn't open. Check your connection and reload the page.";
    return;
  }
  message.disabled = useBook.disabled = practice.disabled = another.disabled = checkButton.disabled = false;
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
  another.addEventListener("click", () => {
    const others = messages.filter((m) => m !== message.value);
    message.value = others[Math.floor(Math.random() * others.length)];
    sendCols = null;
    sendKey = null;
    void send();
  });
  sendLink.addEventListener("click", () => {
    if (!sent) return;
    void copy(challengeUrl(sent.token), "Link copied. Send it to a friend: they'll have to crack your route to read it, and the office tells them when they've got it.", sendStatus);
  });
  sendCopy.addEventListener("click", () => {
    if (!sent) return;
    void copy(sent.cipher.join(" "), `Copied. The key is ${sent.cols} columns, ${sent.key.join(" ")}: send that separately!`, sendStatus);
  });
  practice.addEventListener("change", () => {
    resetCrack();
    crackStatus.textContent = "When the rack reads as a sentence, check the route.";
    void crack(true);
  });
  checkButton.addEventListener("click", () => {
    checks += 1;
    void crack(false, true);
  });
  shareResult.addEventListener("click", () => {
    const text =
      source() === "challenge"
        ? `I cracked your telegram in ${plural(checks, "check")} 📨`
        : `Pier Telegraph, telegram No. ${number}: cracked in ${plural(checks, "check")} 📨\n${location.origin}${location.pathname}`;
    void copy(text, "Copied, with no spoilers. Paste it wherever your friends are.", crackStatus);
  });
  reply.addEventListener("click", () => {
    message.value = "";
    sent = null;
    $("send").scrollIntoView({ behavior: calm() ? "auto" : "smooth", block: "start" });
    message.focus({ preventScroll: true });
    sendStatus.textContent = "Write your telegram. The clerk files it as you type.";
    sendLink.disabled = sendCopy.disabled = true;
  });
  window.addEventListener("hashchange", () => {
    if (!readLink()) return;
    resetCrack();
    void crack(true);
    $("crack").scrollIntoView({ block: "start" });
  });
  // Redraw the route lines when the racks change size (a phone turning, a window resizing).
  const redraw = new ResizeObserver(() => {
    if (sent) drawRoute($("send-rack"), $("send-line") as unknown as SVGSVGElement, $("send-holes") as HTMLOListElement, sent.order, false);
  });
  redraw.observe($("send-rack"));
  const fromLink = readLink();
  await send();
  await crack(true);
  if (fromLink) $("crack").scrollIntoView({ block: "start" });
  else crackStatus.textContent = "When the rack reads as a sentence, check the route.";
}

void start();
