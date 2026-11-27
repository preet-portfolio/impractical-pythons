import "./styles.css";
import "./mirror-spells.css";
import { Python } from "./py/python";
import { mirrorSpellsSources } from "./py/sources";
// The dictionary ships as its own file (not inside the JavaScript) and is fetched at start.
import wordListUrl from "../../projects/04_mirror_spells/data/2of4brif.txt?url";

// Python side of the page: called by the worker as _bridge(fn, args_json) -> JSON.
// The word list is written next to the .py files, so read_words() opens a real file,
// exactly as the command line does.
const BRIDGE = `
import json
from pathlib import Path

import decency
import mirror
import palingrams
import speed_test
import wordlist

WORDS_FILE = Path(wordlist.__file__).parent / "2of4brif.txt"
_words = None

def words():
    """Load and tidy the dictionary once, then reuse it."""
    global _words
    if _words is None:
        _words = wordlist.clean_words(wordlist.read_words(WORDS_FILE))
    return _words

def _bridge(fn, args_json):
    args = json.loads(args_json)
    if fn == "reflect":
        return json.dumps(mirror.reflect(args["text"]))
    if fn == "spellbook":
        book = mirror.spellbook_stats(words())
        shown = decency.family_friendly(book["spells"])
        book["hidden"] = len(book["spells"]) - len(shown)
        book["spells"] = shown
        return json.dumps(book)
    if fn == "pairs":
        pairs = palingrams.two_word_spells(words())
        shown = decency.family_friendly_pairs(pairs)
        return json.dumps({"total": len(pairs), "hidden": len(pairs) - len(shown), "pairs": shown})
    if fn == "race":
        return json.dumps(speed_test.race(words(), args.get("sample", 300)))
    raise ValueError(f"Unknown call {fn!r}")
`;
type Reflection = {
  letters: string;
  reversed: string;
  broken: number | null;
  spell: boolean;
};
type Spellbook = {
  words: number;
  spells: string[];
  count: number;
  percent: number;
  longest: string[];
  by_length: Record<string, number>;
  hidden: number;
};
type Pairs = { total: number; hidden: number; pairs: [string, string][] };
type Race = {
  sample: number;
  words: number;
  slow_seconds: number;
  fast_seconds: number;
  speedup: number;
  slow_full_estimate: number;
  fast_full_seconds: number;
};

const $ = <T extends HTMLElement>(id: string) => document.getElementById(id) as T;
const input = $<HTMLInputElement>("spell");
const forward = $<HTMLOListElement>("forward");
const backward = $<HTMLOListElement>("backward");
const verdict = $("verdict");
const booth = $("booth");
const bookLede = $("book-lede");
const chapters = $("chapters");
const duetLede = $("duet-lede");
const duetCards = $<HTMLUListElement>("duet-cards");
const deal = $<HTMLButtonElement>("deal");
const search = $<HTMLInputElement>("duet-search");
const duetNote = $("duet-note");
const raceButton = $<HTMLButtonElement>("race-start");
const raceResult = $("race-result");
const laneList = $("lane-list");
const laneSet = $("lane-set");
const timeList = $("time-list");
const timeSet = $("time-set");
const hiddenNote = $("hidden-note");

const python = new Python();
let timer = 0;
let request = 0;

function schedule() {
  window.clearTimeout(timer);
  timer = window.setTimeout(() => void look(), 90);
}

async function look() {
  const mine = ++request; // ignore answers to older keystrokes
  let result: Reflection;
  try {
    result = await python.call<Reflection>("reflect", { text: input.value });
  } catch (error) {
    console.error(error);
    verdict.textContent = "The mirror clouded over. Try another word.";
    return;
  }
  if (mine !== request) return;
  show(result);
}

function tiles(list: HTMLOListElement, letters: string, against: string) {
  list.replaceChildren(
    ...[...letters].map((letter, i) => {
      const li = document.createElement("li");
      li.textContent = letter;
      li.className = letter === against[i] ? "match" : "miss";
      return li;
    }),
  );
}

function show(result: Reflection) {
  const { letters, reversed } = result;
  // The CSS shares the row's width between this many tiles, so long phrases still fit.
  booth.style.setProperty("--n", String(Math.max(letters.length, 1)));
  tiles(forward, letters, reversed);
  tiles(backward, reversed, letters);
  booth.classList.toggle("is-spell", result.spell);

  if (!letters) {
    verdict.textContent = "Say a word. Any word.";
  } else if (letters.length === 1) {
    verdict.textContent = "One letter is too easy. The mirror wants at least two.";
    booth.classList.remove("is-spell");
  } else if (result.spell) {
    verdict.textContent = "It's a spell! The mirror agrees with every letter.";
  } else {
    const i = result.broken ?? 0;
    verdict.textContent = `The spell fizzles: ${letters[i].toUpperCase()} meets ${reversed[i].toUpperCase()} in the mirror.`;
  }
}

function cast(word: string) {
  input.value = word;
  void look();
  booth.scrollIntoView({ behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "center" });
}

const CHAPTER_NAMES: Record<number, string> = {
  3: "Three-letter charms",
  4: "Four-letter hexes",
  5: "Five-letter enchantments",
};

function renderSpellbook(book: Spellbook) {
  const oneIn = Math.round(book.words / book.count);
  bookLede.replaceChildren(
    "Out of ",
    strong(book.words.toLocaleString()),
    " words in the dictionary, only ",
    strong(String(book.count)),
    ` are spells: about one in every ${oneIn.toLocaleString()}. The longest is `,
    strong(book.longest.join(" and ")),
    ". Tap any spell to cast it.",
  );
  hiddenRude.words = book.hidden;

  // Group by length, shortest chapter first; six letters and up share the last chapter.
  const groups = new Map<string, string[]>();
  const bySize = [...book.spells].sort((a, b) => Math.min(a.length, 6) - Math.min(b.length, 6));
  for (const spell of bySize) {
    const name = CHAPTER_NAMES[spell.length] ?? "Grand incantations, six letters and up";
    groups.set(name, [...(groups.get(name) ?? []), spell]);
  }
  chapters.replaceChildren(
    ...[...groups].map(([name, spells]) => {
      const section = document.createElement("section");
      section.className = "chapter";
      const heading = document.createElement("h3");
      heading.textContent = `${name} (${spells.length})`;
      const list = document.createElement("ul");
      list.className = "cards";
      for (const spell of spells) {
        const li = document.createElement("li");
        const button = document.createElement("button");
        button.type = "button";
        button.textContent = spell;
        if (book.longest.includes(spell)) button.classList.add("is-longest");
        button.addEventListener("click", () => cast(spell));
        li.append(button);
        list.append(li);
      }
      section.append(heading, list);
      return section;
    }),
  );
}

let allPairs: [string, string][] = [];
const hiddenRude = { words: 0, pairs: 0 };

function pairCard([first, second]: [string, string]) {
  const li = document.createElement("li");
  const button = document.createElement("button");
  button.type = "button";
  button.className = "duet";
  const a = document.createElement("span");
  a.textContent = first;
  const b = document.createElement("span");
  b.textContent = second;
  button.append(a, " ", b);
  button.addEventListener("click", () => cast(`${first} ${second}`));
  li.append(button);
  return li;
}

function dealSix() {
  const hand = [...allPairs];
  // Shuffle just the first six places (a partial Fisher-Yates shuffle).
  for (let i = 0; i < Math.min(6, hand.length); i++) {
    const j = i + Math.floor(Math.random() * (hand.length - i));
    [hand[i], hand[j]] = [hand[j], hand[i]];
  }
  search.value = "";
  duetCards.replaceChildren(...hand.slice(0, 6).map(pairCard));
  duetNote.textContent = "";
}

function findPairs() {
  const needle = search.value.trim().toLowerCase().replace(/[^a-z]/g, "");
  if (!needle) return dealSix();
  const matches = allPairs.filter(([a, b]) => a.includes(needle) || b.includes(needle));
  duetCards.replaceChildren(...matches.slice(0, 48).map(pairCard));
  duetNote.textContent = matches.length
    ? matches.length > 48
      ? `Showing 48 of ${matches.length} spells with "${needle}".`
      : `${matches.length} ${matches.length === 1 ? "spell" : "spells"} with "${needle}".`
    : `No two-word spells with "${needle}". Try fewer letters.`;
}

function renderPairs(data: Pairs) {
  allPairs = data.pairs;
  duetLede.replaceChildren(
    "Some spells need a partner. Say them together and the mirror still agrees. The dictionary hides ",
    strong(data.total.toLocaleString()),
    " of them.",
  );
  hiddenRude.pairs = data.hidden;
  const { words, pairs } = hiddenRude;
  hiddenNote.textContent =
    words || pairs
      ? `A few rude words stay in the dictionary, not on the pier: that keeps ${words} single spells and ${pairs} pairs out of sight.`
      : "";
  deal.disabled = search.disabled = false;
  dealSix();
}

const secs = (s: number) => (s >= 1 ? `${s.toFixed(1)} s` : `${(s * 1000).toFixed(s < 0.01 ? 1 : 0)} ms`);

async function runRace() {
  raceButton.disabled = true;
  raceButton.textContent = "Racing…";
  laneList.style.width = laneSet.style.width = "0%";
  timeList.textContent = timeSet.textContent = "";
  raceResult.textContent = "Both lanes are checking the same 300 words against all 60,000…";
  try {
    const r = await python.call<Race>("race", { sample: 300 });
    laneList.style.width = "100%";
    laneSet.style.width = `${Math.max(1.2, (100 * r.fast_seconds) / r.slow_seconds)}%`;
    timeList.textContent = secs(r.slow_seconds);
    timeSet.textContent = secs(r.fast_seconds);
    raceResult.replaceChildren(
      "The set wins, about ",
      strong(`${Math.round(r.speedup).toLocaleString()} times`),
      ` faster. For the whole dictionary the list would need around ${Math.round(r.slow_full_estimate)} seconds; the set took ${secs(r.fast_full_seconds)}.`,
    );
  } catch (error) {
    console.error(error);
    raceResult.textContent = "Someone tripped at the start line. Try the race again.";
  }
  raceButton.disabled = false;
  raceButton.textContent = "Race again";
}

function strong(text: string) {
  const node = document.createElement("strong");
  node.textContent = text;
  return node;
}

async function start() {
  python.onProgress = (stage) => (verdict.textContent = `${stage}…`);
  try {
    const words = await fetch(wordListUrl).then((response) => {
      if (!response.ok) throw new Error(`Word list: HTTP ${response.status}`);
      return response.text();
    });
    await python.init("mirror_spells", { ...mirrorSpellsSources, "2of4brif.txt": words }, BRIDGE);
  } catch (error) {
    console.error(error);
    verdict.textContent = "The mirror couldn't wake up. Check your connection and reload the page.";
    bookLede.textContent = "";
    return;
  }
  input.addEventListener("input", schedule);
  input.disabled = false;
  input.value = "kayak";
  await look();

  try {
    renderSpellbook(await python.call<Spellbook>("spellbook"));
    renderPairs(await python.call<Pairs>("pairs"));
  } catch (error) {
    console.error(error);
    bookLede.textContent = "The spellbook is stuck shut. Reload the page to try again.";
    return;
  }
  deal.addEventListener("click", dealSix);
  search.addEventListener("input", findPairs);
  raceButton.addEventListener("click", () => void runRace());
  raceButton.disabled = false;
}

void start();
