import "./styles.css";
import "./postcard-rack.css";
import { Python } from "./py/python";
import { commonSources, postcardRackSources } from "./py/sources";
// The dictionary ships as its own file and is fetched at start: every look needs it.
import wordListUrl from "../../projects/common/data/2of4brif.txt?url";

// Python side of the page: called by the worker as _bridge(fn, args_json) -> JSON.
// The page never finds a letter itself: it asks Python where the glass lands.
const BRIDGE = `
import json
from datetime import date
from pathlib import Path

import decency
import null_finder
import postcards
import word_gaps
import wordlist

WORDS_FILE = Path(wordlist.__file__).parent / "2of4brif.txt"
_cache = {}

def words():
    """Load and tidy the dictionary once: nothing rude, no stray single letters."""
    if "words" not in _cache:
        tidy = wordlist.clean_words(wordlist.read_words(WORDS_FILE))
        _cache["words"] = word_gaps.word_set(decency.family_friendly(tidy))
    return _cache["words"]

def rack(args):
    today = postcards.todays_postcard(date.fromisoformat(args["today"]))
    words()  # warm up the dictionary while the visitor reads the card
    return {"cards": postcards.POSTCARDS, "today": today["id"],
            "number": postcards.postcard_number(date.fromisoformat(args["today"])),
            "rules": {rule: null_finder.describe(rule, 1) for rule in null_finder.RULES}}

def look(args):
    text, rule, offset = args["text"], args["rule"], args["offset"]
    positions = null_finder.picked_positions(text, rule, offset)
    letters = "".join(text[i] for i in positions).lower()
    reading = null_finder.read_reading(letters, words()) if letters else {
        "words": [], "coverage": 0, "word_length": 0, "reads": False}
    return {"positions": positions, "letters": letters,
            "setting": null_finder.describe(rule, offset)} | reading

def scan(args):
    return null_finder.scan(args["text"], words())

CALLS = {"rack": rack, "look": look, "scan": scan}

def _bridge(fn, args_json):
    if fn in CALLS:
        return json.dumps(CALLS[fn](json.loads(args_json)))
    raise ValueError(f"Unknown call {fn!r}")
`;

type Card = {
  id: string;
  place: string;
  scene: string;
  to: string;
  sender: string;
  text: string;
  rule: string | null;
  offset: number;
  note: string;
};
type Rack = { cards: Card[]; today: string; number: number; rules: Record<string, string> };
type Look = {
  positions: number[];
  letters: string;
  setting: string;
  words: string[];
  coverage: number;
  word_length: number;
  reads: boolean;
};
type Reading = Look & { rule: string; offset: number };

const $ = <T extends HTMLElement>(id: string) => document.getElementById(id) as T;
const python = new Python();
const calm = () => matchMedia("(prefers-reduced-motion: reduce)").matches;

const RULE_NAMES: Record<string, string> = {
  punctuation: "Punctuation",
  words: "Every word",
  capitals: "Capital words",
};
const MOST = 6;
const SHORTEST = 6; // null_finder.SHORTEST: fewer letters than this never count as a note
const OWN = "own"; // the blank card for the visitor's own text

const cardText = $("card-text");
const cardOwn = $<HTMLTextAreaElement>("card-own");
const status = $("status");
const foundStamp = $("found-stamp");
const scanList = $<HTMLOListElement>("scan-list");

let cards: Card[] = [];
let todayId = "";
let current: Card | null = null;
let rule = "punctuation";
let offset = 1;
let request = 0;
let timer = 0;

const text = () => (current ? current.text : cardOwn.value);
const today = () => new Date().toLocaleDateString("en-CA"); // the visitor's own date

function button(label: string, className: string, onClick: () => void) {
  const b = document.createElement("button");
  b.type = "button";
  b.className = className;
  b.textContent = label;
  b.addEventListener("click", onClick);
  return b;
}

/**
 * Write the card's message with the picked letters marked, one <mark> per letter.
 * Each word is wrapped in its own span so a marked letter never breaks off onto a new line.
 */
function renderText(message: string, picked: number[]) {
  const marks = new Set(picked);
  let word: HTMLSpanElement | null = null;
  let run = "";
  let marked = 0;
  const flush = () => {
    if (run) (word ?? cardText).append(run);
    run = "";
  };
  cardText.replaceChildren();
  [...message].forEach((char, i) => {
    if (/\s/.test(char)) {
      flush();
      word = null;
      run = char;
      return;
    }
    if (!word) {
      flush();
      word = document.createElement("span");
      word.className = "word";
      cardText.append(word);
    }
    if (!marks.has(i)) {
      run += char;
      return;
    }
    flush();
    const mark = document.createElement("mark");
    mark.textContent = char;
    if (!calm()) mark.style.animationDelay = `${Math.min(marked++, 40) * 18}ms`;
    word.append(mark);
  });
  flush();
}

function renderRules() {
  $("rules").replaceChildren(
    ...Object.keys(RULE_NAMES).map((name) => {
      const b = button(RULE_NAMES[name], "rule", () => {
        rule = name;
        renderRules();
        void look();
      });
      b.setAttribute("aria-pressed", String(name === rule));
      return b;
    }),
  );
}

function renderOffset() {
  $("offset").textContent = String(offset);
  $<HTMLButtonElement>("fewer").disabled = offset <= 1;
  $<HTMLButtonElement>("more").disabled = offset >= MOST;
}

function stamp(show: boolean) {
  foundStamp.hidden = !show;
  foundStamp.classList.remove("is-landing");
  if (show && !calm()) {
    void foundStamp.offsetWidth; // restart the animation
    foundStamp.classList.add("is-landing");
  }
}

/** What the luggage tag says about the letters: a note, a fluke, or soup. */
function verdict(result: Look) {
  if (result.reads) return `“${result.words.join(" ")}”`;
  const share = Math.round(result.coverage * 100);
  if (share < 95) return `Alphabet soup: only ${share}% of it makes words.`;
  if (result.letters.length < SHORTEST) return `“${result.words.join(" ")}”, but that's too few letters to call it a message.`;
  return `“${result.words.join(" ")}”: real words, but tiny ones. That's what luck looks like.`;
}

async function look() {
  const mine = ++request;
  renderOffset();
  try {
    const result = await python.call<Look>("look", { text: text(), rule, offset });
    if (mine !== request) return;
    $("setting").textContent = `Reading the ${result.setting}.`;
    if (current) renderText(current.text, result.positions);
    $("tag-letters").textContent = result.letters || "Nothing here: this setting picks no letters.";
    const reads = result.reads;
    $("tag-words").textContent = result.letters ? verdict(result) : "";
    $("tag-words").classList.toggle("is-found", reads);
    stamp(reads);
    if (reads) {
      status.textContent = current
        ? `There it is! ${current.sender} hid a note in the ${result.setting}.`
        : `Something reads in the ${result.setting}. Was it hidden on purpose, or just luck?`;
    } else {
      status.textContent = current?.note
        ? "Nothing yet. Turn the dial, or try counting from somewhere else."
        : current
          ? "Nothing reads with this setting. Maybe there's nothing to find."
          : "Type or paste any text on the card, then turn the dial.";
    }
  } catch (error) {
    console.error(error);
    status.textContent = "The glass slipped. Try that again.";
  }
}

async function scanAll() {
  try {
    const readings = await python.call<Reading[]>("scan", { text: text() });
    const found = readings.filter((r) => r.reads);
    scanList.replaceChildren(
      ...readings.slice(0, 6).map((reading) => {
        const li = document.createElement("li");
        li.className = reading.reads ? "scan-row is-found" : "scan-row";
        const head = document.createElement("p");
        head.className = "scan-head";
        head.textContent = `${reading.setting}: ${Math.round(reading.coverage * 100)}% real words`;
        const words = document.createElement("p");
        words.className = "scan-words";
        words.textContent = reading.words.join(" ");
        const use = button("Set the glass to this", "paper-button", () => {
          rule = reading.rule;
          offset = reading.offset;
          renderRules();
          void look();
          $("card").scrollIntoView({ behavior: calm() ? "auto" : "smooth", block: "center" });
        });
        li.append(head, words, use);
        return li;
      }),
    );
    status.textContent = found.length
      ? `Tried ${readings.length} settings. ${found.length === 1 ? "One reads" : `${found.length} read`} as real words.`
      : readings.length
        ? `Tried ${readings.length} settings and none reads as a message. It might just be a postcard.`
        : "Not enough letters on the card to try anything yet.";
  } catch (error) {
    console.error(error);
    status.textContent = "The glass slipped. Try that again.";
  }
}

/** Put a card (or the blank one) on the desk, with the glass back at the start. */
function show(id: string) {
  current = cards.find((card) => card.id === id) ?? null;
  rule = "punctuation";
  offset = 1;
  scanList.replaceChildren();
  const own = !current;
  cardOwn.hidden = !own;
  cardText.hidden = own;
  const card = $("card");
  card.dataset.scene = current?.scene ?? "own";
  $("card-label").textContent = own ? "Your own words" : id === todayId ? "Today's postcard" : `A card from ${current!.place}`;
  // Some senders write their own "Dear ..." and "love ...": don't say it twice.
  const message = current?.text.toLowerCase() ?? "";
  $("card-to").textContent = own
    ? "Paste a letter, a poem or a song you suspect:"
    : message.startsWith("dear ")
      ? ""
      : `Dear ${current!.to},`;
  $("card-from").textContent = own || message.includes("love ") ? "" : `Love from ${current!.sender} x`;
  $("postmark").textContent = own ? "YOUR TOWN" : current!.place.toUpperCase();
  renderRules();
  renderRack();
  void look();
}

function renderRack() {
  const items = [...cards.filter((c) => c.id === todayId), ...cards.filter((c) => c.id !== todayId)];
  $("rack").replaceChildren(
    ...items.map((card) => {
      const li = document.createElement("li");
      const b = button("", "front", () => {
        show(card.id);
        $("card").focus({ preventScroll: true });
        $("card").scrollIntoView({ behavior: calm() ? "auto" : "smooth", block: "start" });
      });
      b.dataset.scene = card.scene;
      b.setAttribute("aria-pressed", String(current?.id === card.id));
      b.setAttribute("aria-label", `Postcard from ${card.place}${card.id === todayId ? ", today's card" : ""}`);
      const greet = document.createElement("span");
      greet.className = "front-greet";
      greet.textContent = "Greetings from";
      const place = document.createElement("span");
      place.className = "front-place";
      place.textContent = card.place;
      b.append(greet, place);
      if (card.id === todayId) {
        const badge = document.createElement("span");
        badge.className = "front-today";
        badge.textContent = "Today";
        b.append(badge);
      }
      li.append(b);
      return li;
    }),
    (() => {
      const li = document.createElement("li");
      const b = button("", "front front-own", () => {
        show(OWN);
        cardOwn.focus();
      });
      b.setAttribute("aria-pressed", String(current === null));
      const place = document.createElement("span");
      place.className = "front-place";
      place.textContent = "Your own words";
      b.append(place);
      li.append(b);
      return li;
    })(),
  );
}

// The first visit downloads Python, which takes a few seconds: say so, in the shop's voice.
const STAGES: Record<string, string> = {
  "Downloading Python": "Unlocking the shop. The first visit takes a few seconds…",
  "Loading the project": "Spinning the rack…",
};

async function start() {
  python.onProgress = (stage) => (status.textContent = STAGES[stage] ?? `${stage}…`);
  let rack: Rack;
  try {
    const words = await fetch(wordListUrl).then((response) => {
      if (!response.ok) throw new Error(`Dictionary: ${response.status}`);
      return response.text();
    });
    await python.init("postcard_rack", { ...commonSources, ...postcardRackSources, "2of4brif.txt": words }, BRIDGE);
    status.textContent = "Sorting the postcards…";
    rack = await python.call<Rack>("rack", { today: today() });
  } catch (error) {
    console.error(error);
    status.textContent = "The shop couldn't open. Check your connection and reload the page.";
    return;
  }
  cards = rack.cards;
  todayId = rack.today;
  $<HTMLButtonElement>("scan").disabled = false;
  $("fewer").addEventListener("click", () => {
    offset = Math.max(1, offset - 1);
    void look();
  });
  $("more").addEventListener("click", () => {
    offset = Math.min(MOST, offset + 1);
    void look();
  });
  $("scan").addEventListener("click", () => void scanAll());
  cardOwn.addEventListener("input", () => {
    window.clearTimeout(timer);
    scanList.replaceChildren();
    timer = window.setTimeout(() => void look(), 200);
  });
  show(todayId);
}

void start();
