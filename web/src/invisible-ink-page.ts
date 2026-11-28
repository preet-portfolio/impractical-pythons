import "./styles.css";
import "./invisible-ink.css";
import { Python } from "./py/python";
import { commonSources, invisibleInkSources } from "./py/sources";

// Python side of the page: called by the worker as _bridge(fn, args_json) -> JSON.
// Python scrambles, hides, builds the Word file and reads one back; the page only draws.
const BRIDGE = `
import base64
import json

import docx_reader
import docx_writer
import invisible_ink as ink
import letters
import vigenere

def problem(error):
    return {"problem": str(error)}

def demo(args):
    return {"title": letters.TITLE, "subtitle": letters.SUBTITLE, "date": letters.DATE,
            "letter": letters.demo_letter()}

def unscramble(args):
    """Unscramble the ink lines with a key; for the shop's own letter, say if it's the right one."""
    try:
        key = vigenere.clean_key(args["key"])
    except vigenere.KeyProblem as error:
        return problem(error)
    lines = [vigenere.decrypt(line, key) for line in args["lines"]]
    first = args["lines"][0] if args["lines"] else ""
    return {"lines": lines, "key": key, "over": vigenere.key_over(first, key),
            "solved": args.get("demo") and key == letters.KEY}

def prepare(args):
    cover = ink.letter_lines(args["cover"])
    secret = ink.secret_lines(args["secret"])
    if args.get("spell"):
        secret = [vigenere.spell_out(line) for line in secret]
    return cover, secret

def room(args):
    cover, secret = prepare(args)
    return ink.room_check(cover, secret) | {"long": ink.long_lines(secret)}

def hide(args):
    title = " ".join(args.get("title", "").split()) or "Seaview Cottage"
    try:
        for text, what in ((args["cover"], "letter"), (args["secret"], "secret"), (title, "letterhead")):
            ink.check_text(text, what)
        if not args["cover"].strip() or not args["secret"].strip():
            return {"problem": "Write the letter and the secret first."}
        key = vigenere.clean_key(args["key"])
        cover, secret = prepare(args)
        letter = ink.interleave(cover, [vigenere.encrypt(line, key) for line in secret])
    except ValueError as error:
        return problem(error)
    return {"title": title, "letter": letter, "key": key, "token": ink.pack_letter(letter, title)}

def unpack(args):
    try:
        return ink.unpack_letter(args["token"])
    except ink.InkProblem as error:
        return problem(error)

def word_file(args):
    data = docx_writer.make_docx(args["letter"], args["title"], args.get("subtitle", ""), args.get("date", ""))
    return {"data": base64.b64encode(data).decode("ascii")}

def find(args):
    try:
        found = docx_reader.find_white_ink(base64.b64decode(args["data"]))
    except docx_reader.NotALetter as error:
        return problem(error)
    return {"ink": found}

def typewriter(args):
    try:
        ink.check_text(args["cover"] + " " + args["secret"], "line")
        return {"pieces": ink.between_words(args["cover"], args["secret"])}
    except ink.InkProblem as error:
        return problem(error)

CALLS = {"demo": demo, "unscramble": unscramble, "room": room, "hide": hide, "unpack": unpack,
         "word_file": word_file, "find": find, "typewriter": typewriter}

def _bridge(fn, args_json):
    if fn in CALLS:
        return json.dumps(CALLS[fn](json.loads(args_json)))
    raise ValueError(f"Unknown call {fn!r}")
`;

type Line = { text: string; hidden: boolean };
type Letter = { title: string; subtitle?: string; date?: string; letter: Line[] };
type Problem = { problem?: string };
type Unscrambled = { lines: string[]; key: string; over: string; solved: boolean } & Problem;
type Room = { fits: boolean; blanks: number; needed: number; add: number; long: number[] };
type Hidden = Letter & { key: string; token: string } & Problem;
type Piece = { text: string; hidden: boolean };

const $ = <T extends HTMLElement>(id: string) => document.getElementById(id) as T;
const python = new Python();
const calm = () => matchMedia("(prefers-reduced-motion: reduce)").matches;

const status = $("status");
const deskStatus = $("desk-status");
const letterEl = $("letter");
const lampZone = $("lamp-zone");

type Source = "demo" | "own" | "received";
let source: Source = "demo";
let shown: Letter = { title: "", letter: [] };
let ownKey = ""; // the key of the visitor's own letter, never sent anywhere
let token = "";
let decoded: string[] | null = null; // the ink, unscrambled, once the right key is in

// ---------------------------------------------------------------- the letter

function sheet(target: HTMLElement, letter: Letter, ink: string[] | null) {
  const head = document.createElement("header");
  head.className = "letterhead";
  const title = document.createElement("p");
  title.className = "letterhead-title";
  title.textContent = letter.title;
  head.append(title);
  if (letter.subtitle) {
    const sub = document.createElement("p");
    sub.className = "letterhead-sub";
    sub.textContent = letter.subtitle;
    head.append(sub);
  }
  const body = document.createElement("div");
  body.className = "letter-body";
  if (letter.date) {
    const date = document.createElement("p");
    date.className = "line date";
    const when = document.createElement("span");
    when.textContent = letter.date;
    date.append(when);
    body.append(date);
  }
  let n = 0;
  for (const line of letter.letter) {
    const p = document.createElement("p");
    const span = document.createElement("span");
    if (line.hidden) {
      p.className = "line ink";
      span.textContent = ink ? ink[n] : line.text;
      n += 1;
    } else {
      p.className = line.text ? "line" : "line blank";
      span.textContent = line.text || " ";
    }
    p.append(span);
    body.append(p);
  }
  target.replaceChildren(head, body);
}

function drawLetter() {
  sheet($("sheet"), shown, decoded);
  sheet($("sheet-uv"), shown, decoded);
  letterEl.classList.toggle("is-decoded", decoded !== null);
}

const inkLines = () => shown.letter.filter((line) => line.hidden).map((line) => line.text);

function putOnCounter(letter: Letter, from: Source) {
  shown = letter;
  source = from;
  decoded = null;
  $("strip").hidden = true;
  $<HTMLInputElement>("key").value = "";
  $("key-help").textContent = "";
  $("hint").hidden = from !== "demo";
  $("back-to-demo").hidden = from === "demo";
  $("letter-label").textContent = from === "demo" ? "On the counter" : from === "own" ? "Your letter" : "A letter for you";
  drawLetter();
}

// ------------------------------------------------------------- the UV lamp

let lampOn = false;

function setLamp(on: boolean) {
  lampOn = on;
  letterEl.classList.toggle("is-lit", on);
  $("lamp").setAttribute("aria-pressed", String(on));
  $("lamp").textContent = on ? "Switch off the lamp" : "Switch on the lamp";
}

/** The torch: a circle of UV light that follows the pointer (or sits where a finger taps). */
function moveTorch(event: PointerEvent) {
  const box = letterEl.getBoundingClientRect();
  letterEl.style.setProperty("--x", `${event.clientX - box.left}px`);
  letterEl.style.setProperty("--y", `${event.clientY - box.top}px`);
  letterEl.classList.add("has-torch");
}

lampZone.addEventListener("pointermove", (event) => {
  if (event.pointerType === "mouse") moveTorch(event);
});
lampZone.addEventListener("pointerdown", moveTorch);
lampZone.addEventListener("pointerleave", (event) => {
  if (event.pointerType === "mouse") letterEl.classList.remove("has-torch");
});

// ------------------------------------------------------------- the key

const HINT = "A seabird with a bright stripy beak, six letters. It nests on cliffs.";

async function unscramble(event: Event) {
  event.preventDefault();
  const keyInput = $<HTMLInputElement>("key");
  const result = await python.call<Unscrambled>("unscramble", {
    lines: inkLines(),
    key: keyInput.value,
    demo: source === "demo",
  });
  if (result.problem) {
    $("key-help").textContent = result.problem;
    keyInput.focus();
    return;
  }
  drawStrip(inkLines()[0] ?? "", result.over, result.lines[0] ?? "");
  const right = source === "demo" ? result.solved : source === "own" ? result.key === ownKey : null;
  if (right === false) {
    decoded = null;
    drawLetter();
    $("key-help").textContent = `${result.key} turns it into more nonsense. Try another word.`;
    status.textContent = "Still scrambled. The strip below shows what that key does to the first line.";
    return;
  }
  decoded = result.lines;
  drawLetter();
  setLamp(true);
  $("key-help").textContent = right ? `${result.key} is the key.` : `Unscrambled with ${result.key}. If it reads as words, that's the one.`;
  status.textContent = source === "demo"
    ? "Cracked! Somebody's fixing the duck race. Read it under the lamp."
    : "Unscrambled. Read it under the lamp.";
}

/** Key over scrambled over plain, one box per letter, like a page from a cipher notebook. */
function drawStrip(scrambled: string, over: string, plain: string) {
  const count = Math.min(scrambled.length, 34);
  const row = (text: string, name: string, label: string) => {
    const r = document.createElement("div");
    r.className = `strip-row ${name}`;
    const tag = document.createElement("span");
    tag.className = "strip-tag";
    tag.textContent = label;
    r.append(tag);
    for (const ch of text.slice(0, count)) {
      const cell = document.createElement("span");
      cell.className = ch.trim() ? "cell" : "cell gap";
      cell.textContent = ch;
      r.append(cell);
    }
    if (text.length > count) r.append("…");
    return r;
  };
  $("strip-rows").replaceChildren(row(over, "key-row", "key"), row(scrambled, "ink-row", "ink"), row(plain, "plain-row", "reads"));
  $("strip").hidden = false;
}

// --------------------------------------------------- how it gets caught

function caught(button: HTMLButtonElement) {
  const mode = button.dataset.caught!;
  const on = button.getAttribute("aria-pressed") !== "true";
  button.setAttribute("aria-pressed", String(on));
  letterEl.classList.toggle(`caught-${mode}`, on);
  const says: Record<string, string> = {
    select: "Selected: the bars on the blank lines are different lengths. Blank lines shouldn't be.",
    spell: "The spellchecker underlines words nobody can see. Scrambled words aren't in any dictionary.",
    plain: "Saved as plain text, the colour is gone and the ink is just more words.",
  };
  $("caught-help").textContent = on ? says[mode] : "Each one is a slip that gives the ink away.";
}

// ------------------------------------------------------- write your own

const coverInput = $<HTMLTextAreaElement>("cover");
const secretInput = $<HTMLTextAreaElement>("secret");
const spellInput = $<HTMLInputElement>("spell");

const EXAMPLE_COVER = `Dear Nan,

The weather is lovely and the sea is warmer than last year.

We had chips on the harbour wall, and a gull stole one.

Kit has learned to skim stones. Five bounces!

See you on Sunday.

Love,
Sam`;
const EXAMPLE_SECRET = `The spare key is in the teapot.
Feed the cat at 6.
Do not let Kit near the biscuits.`;

let roomTimer = 0;
let addNeeded = 0;

async function checkRoom() {
  const result = await python.call<Room>("room", {
    cover: coverInput.value,
    secret: secretInput.value,
    spell: spellInput.checked,
  });
  addNeeded = result.add;
  const gaps = `${result.blanks} blank line${result.blanks === 1 ? "" : "s"}`;
  const needs = `${result.needed} line${result.needed === 1 ? "" : "s"}`;
  let say = !result.needed
    ? `The letter has ${gaps} to hide things in.`
    : result.fits
      ? `${gaps} in the letter, the secret needs ${needs}. Plenty of room.`
      : `The secret needs ${needs}, but the letter only has ${gaps}. Add ${result.add} more.`;
  if (result.long.length) say += ` Line ${result.long.join(", ")} of the secret is long and may wrap: split it.`;
  $("room").textContent = say;
  $("room").classList.toggle("is-short", !result.fits);
  $("add-room").hidden = result.fits;
}

function roomSoon() {
  window.clearTimeout(roomTimer);
  roomTimer = window.setTimeout(() => void checkRoom(), 250);
}

/** The book's tip: press Enter a few more times under the signature. */
function addRoom() {
  coverInput.value = coverInput.value.replace(/\n*$/, "\n") + "\n".repeat(addNeeded);
  void checkRoom();
  coverInput.focus();
}

async function hideSecret(event: Event) {
  event.preventDefault();
  const result = await python.call<Hidden>("hide", {
    cover: coverInput.value,
    secret: secretInput.value,
    key: $<HTMLInputElement>("new-key").value,
    spell: spellInput.checked,
    title: $<HTMLInputElement>("letterhead").value,
  });
  if (result.problem) {
    deskStatus.textContent = result.problem;
    return;
  }
  ownKey = result.key;
  token = result.token;
  $("share").hidden = false;
  putOnCounter({ title: result.title, letter: result.letter }, "own");
  setLamp(false);
  deskStatus.textContent = `Done! It's on the counter. Your key is ${result.key}: tell it to your friend in person, never in the link.`;
  status.textContent = "Your letter looks as dull as can be. Shine the lamp to see the ink.";
  letterEl.focus({ preventScroll: true });
  letterEl.scrollIntoView({ behavior: calm() ? "auto" : "smooth", block: "start" });
}

async function share() {
  const link = `${location.origin}${location.pathname}#letter=${token}`;
  try {
    await navigator.clipboard.writeText(link);
    deskStatus.textContent = "Link copied. It holds the letter and the scrambled ink, but not the key.";
  } catch {
    deskStatus.textContent = `Copy this link: ${link}`;
  }
}

async function openFromLink() {
  const match = /^#letter=([A-Za-z0-9_-]+)$/.exec(location.hash);
  if (!match) return false;
  const result = await python.call<Letter & Problem>("unpack", { token: match[1] });
  if (result.problem) {
    status.textContent = result.problem;
    return false;
  }
  putOnCounter(result, "received");
  setLamp(false);
  status.textContent = "Someone sent you this letter. Shine the lamp, then try the key word they told you.";
  return true;
}

// ----------------------------------------------------------- the Word file

async function download() {
  const { data } = await python.call<{ data: string }>("word_file", {
    letter: shown.letter,
    title: shown.title,
    subtitle: shown.subtitle ?? "",
    date: shown.date ?? "",
  });
  const bytes = Uint8Array.from(atob(data), (c) => c.charCodeAt(0));
  const blob = new Blob([bytes], { type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = source === "demo" ? "booking-confirmation.docx" : "letter.docx";
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
  status.textContent = "Saved. In Word, select everything and highlight it in black: the white ink shows up.";
}

// ------------------------------------------------------ the typewriter

let typeTimer = 0;

async function typeLine() {
  const result = await python.call<{ pieces?: Piece[] } & Problem>("typewriter", {
    cover: $<HTMLInputElement>("type-cover").value,
    secret: $<HTMLInputElement>("type-secret").value,
  });
  if (result.problem || !result.pieces) {
    $("type-status").textContent = result.problem ?? "";
    return;
  }
  const hidden = result.pieces.filter((p) => p.hidden).length;
  $("type-status").textContent = hidden
    ? `${hidden} letter${hidden === 1 ? "" : "s"} hiding in the spaces.`
    : "Type something to hide in the spaces.";
  $("type-line").replaceChildren(
    ...result.pieces.map((piece) => {
      if (!piece.hidden) return document.createTextNode(piece.text);
      const span = document.createElement("span");
      span.className = "type-ink";
      span.textContent = piece.text;
      return span;
    }),
  );
}

// ----------------------------------------------------------- the detector

const toBase64 = (buffer: ArrayBuffer) => {
  let text = "";
  const bytes = new Uint8Array(buffer);
  for (let i = 0; i < bytes.length; i += 0x8000) text += String.fromCharCode(...bytes.subarray(i, i + 0x8000));
  return btoa(text);
};

let foundInk: string[] = [];

async function check(file: File | undefined) {
  if (!file) return;
  $("find-status").textContent = `Looking inside ${file.name}…`;
  $("found").replaceChildren();
  $("find-key-form").hidden = true;
  if (file.size > 5_000_000) {
    $("find-status").textContent = "That file is far too big to be a letter.";
    return;
  }
  const result = await python.call<{ ink?: string[] } & Problem>("find", { data: toBase64(await file.arrayBuffer()) });
  if (result.problem || !result.ink) {
    $("find-status").textContent = result.problem ?? "";
    return;
  }
  foundInk = result.ink;
  $("find-status").textContent = foundInk.length
    ? `Found ink on ${foundInk.length} line${foundInk.length === 1 ? "" : "s"}:`
    : "No white ink in that letter. It really is just a letter.";
  showFound(foundInk);
  $("find-key-form").hidden = foundInk.length === 0;
}

function showFound(lines: string[]) {
  $("found").replaceChildren(
    ...lines.map((line) => {
      const li = document.createElement("li");
      li.textContent = line;
      return li;
    }),
  );
}

async function unscrambleFound(event: Event) {
  event.preventDefault();
  const result = await python.call<Unscrambled>("unscramble", { lines: foundInk, key: $<HTMLInputElement>("find-key").value });
  if (result.problem) {
    $("find-status").textContent = result.problem;
    return;
  }
  showFound(result.lines);
  $("find-status").textContent = `Unscrambled with ${result.key}. If it reads as words, that's the key.`;
}

// ------------------------------------------------------------- start up

const STAGES: Record<string, string> = {
  "Downloading Python": "Unlocking the shop. The first visit takes a few seconds…",
  "Loading the project": "Mixing the ink…",
};

async function start() {
  python.onProgress = (stage) => (status.textContent = STAGES[stage] ?? `${stage}…`);
  let demo: Letter;
  try {
    await python.init("invisible_ink", { ...commonSources, ...invisibleInkSources }, BRIDGE);
    demo = await python.call<Letter>("demo");
  } catch (error) {
    console.error(error);
    status.textContent = "The shop couldn't open. Check your connection and reload the page.";
    return;
  }
  putOnCounter(demo, "demo");
  status.textContent = "Looks like a dull booking letter. Shine the lamp on it.";

  $("lamp").addEventListener("click", () => setLamp(!lampOn));
  $("key-form").addEventListener("submit", (event) => void unscramble(event));
  $("hint").addEventListener("click", () => ($("key-help").textContent = HINT));
  for (const b of document.querySelectorAll<HTMLButtonElement>("[data-caught]")) b.addEventListener("click", () => caught(b));
  $("download").addEventListener("click", () => void download());
  $("back-to-demo").addEventListener("click", () => {
    history.replaceState(null, "", location.pathname);
    putOnCounter(demo, "demo");
    setLamp(false);
    status.textContent = "Back to the shop's own letter.";
  });

  coverInput.value = EXAMPLE_COVER;
  secretInput.value = EXAMPLE_SECRET;
  for (const field of [coverInput, secretInput]) field.addEventListener("input", roomSoon);
  spellInput.addEventListener("change", roomSoon);
  $("add-room").addEventListener("click", addRoom);
  $("hide-form").addEventListener("submit", (event) => void hideSecret(event));
  $("share").addEventListener("click", () => void share());

  $<HTMLInputElement>("type-cover").value = "LOST PROPERTY: one umbrella, two buckets, a single flip flop and a very cross crab.";
  $<HTMLInputElement>("type-secret").value = "KEYINBOOT";
  for (const id of ["type-cover", "type-secret"]) {
    $(id).addEventListener("input", () => {
      window.clearTimeout(typeTimer);
      typeTimer = window.setTimeout(() => void typeLine(), 200);
    });
  }
  $("type-lamp").addEventListener("click", () => {
    const on = $("type-lamp").getAttribute("aria-pressed") !== "true";
    $("type-lamp").setAttribute("aria-pressed", String(on));
    $("type-lamp").textContent = on ? "Switch off the lamp" : "Shine the lamp on it";
    $("type-card").classList.toggle("is-lit", on);
  });

  const fileInput = $<HTMLInputElement>("file");
  fileInput.addEventListener("change", () => void check(fileInput.files?.[0]));
  const drop = $("drop");
  drop.addEventListener("dragover", (event) => {
    event.preventDefault();
    drop.classList.add("is-over");
  });
  drop.addEventListener("dragleave", () => drop.classList.remove("is-over"));
  drop.addEventListener("drop", (event) => {
    event.preventDefault();
    drop.classList.remove("is-over");
    void check(event.dataTransfer?.files[0]);
  });
  $("find-key-form").addEventListener("submit", (event) => void unscrambleFound(event));

  for (const id of ["lamp", "key", "unscramble", "download", "letterhead", "cover", "secret", "new-key", "spell", "hide", "type-lamp", "type-cover", "type-secret", "file"]) {
    $<HTMLInputElement>(id).disabled = false;
  }
  window.addEventListener("hashchange", () => void openFromLink());
  await Promise.all([checkRoom(), typeLine(), openFromLink()]);
}

void start();
