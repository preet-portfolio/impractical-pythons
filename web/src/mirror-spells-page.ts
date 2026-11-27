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

import mirror
import wordlist

WORDS = Path(wordlist.__file__).parent / "2of4brif.txt"

def _bridge(fn, args_json):
    args = json.loads(args_json)
    if fn == "reflect":
        return json.dumps(mirror.reflect(args["text"]))
    if fn == "spellbook":
        return json.dumps(mirror.spellbook_stats(wordlist.read_words(WORDS)))
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
};

const $ = <T extends HTMLElement>(id: string) => document.getElementById(id) as T;
const input = $<HTMLInputElement>("spell");
const forward = $<HTMLOListElement>("forward");
const backward = $<HTMLOListElement>("backward");
const verdict = $("verdict");
const booth = $("booth");
const bookLede = $("book-lede");
const chapters = $("chapters");

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
  } catch (error) {
    console.error(error);
    bookLede.textContent = "The spellbook is stuck shut. Reload the page to try again.";
  }
}

void start();
