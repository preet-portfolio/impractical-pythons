import "./styles.css";
import "./shuffle-cafe.css";
import { Python } from "./py/python";
import { commonSources, shuffleCafeSources } from "./py/sources";
import { startChef } from "./shuffle-cafe-chef";
import { startPhrases } from "./shuffle-cafe-phrase";
import { startSieve } from "./shuffle-cafe-sieve";
// The dictionary ships as its own file (not inside the JavaScript) and is fetched at start.
import wordListUrl from "../../projects/common/data/2of4brif.txt?url";

// Python side of the page: called by the worker as _bridge(fn, args_json) -> JSON.
// The families index is built once, the first time it's needed, then every lookup is instant.
const BRIDGE = `
import json
from pathlib import Path

import anagrams
import chef
import decency
import leftovers
import ngrams
import phrases
import sieve
import wordlist

WORDS_FILE = Path(wordlist.__file__).parent / "2of4brif.txt"
_cache = {}

def words():
    """Load and tidy the dictionary once, then reuse it."""
    if "words" not in _cache:
        _cache["words"] = wordlist.clean_words(wordlist.read_words(WORDS_FILE))
    return _cache["words"]

def families():
    """File every word under its sorted letters, once."""
    if "families" not in _cache:
        _cache["families"] = anagrams.anagram_families(words())
    return _cache["families"]

def letter_stats():
    """Count pairs, triples and shapes once, for the sieve."""
    if "stats" not in _cache:
        _cache["stats"] = sieve.LetterStats(words())
    return _cache["stats"]

def strained(letters, active):
    """Strain the letters and add the pair chart; rude made-up words stay hidden."""
    if len(letters) > sieve.SIEVE_LIMIT:
        return {"letters": letters, "too_many": True}
    report = sieve.strain(letters, letter_stats(), tuple(active))
    shown = decency.nothing_rude_inside(report["survivors"])
    report["hidden"] = len(report["survivors"]) - len(shown)
    report["survivors"] = shown
    by_letter = {}
    for word in shown:
        by_letter[word[0]] = by_letter.get(word[0], 0) + 1
    report["by_letter"] = dict(sorted(by_letter.items()))
    table = ngrams.pair_table(letters, letter_stats().pairs)
    report["pairs"] = [
        {"pair": pair, "share": share, "rare": letter_stats().rare_pair(pair)}
        for pair, share in table.items()
    ]
    return report

def _bridge(fn, args_json):
    args = json.loads(args_json)
    if fn == "shuffle":
        found = anagrams.anagrams_from_families(args["text"], families())
        shown = decency.family_friendly(found)
        letters = anagrams.letters_only(args["text"])
        return json.dumps({"letters": letters, "anagrams": shown, "hidden": len(found) - len(shown)})
    if fn == "families":
        stats = anagrams.menu_stats(words(), families())
        friendly = {key: decency.family_friendly(fam) for key, fam in families().items()}
        stats["hidden"] = sum(len(fam) - len(friendly[key]) for key, fam in families().items())
        friendly = {key: fam for key, fam in friendly.items() if len(fam) > 1}
        stats["top"] = anagrams.biggest_families(friendly, args.get("count", 8))
        del stats["biggest"]  # the unfiltered biggest family has a rude word in it
        return json.dumps(stats)
    if fn == "phrase":
        status = phrases.phrase_status(args["name"], args["chosen"], words())
        if status is None:
            return json.dumps(None)
        status["options"] = decency.family_friendly(status["options"])
        return json.dumps(status)
    if fn == "leftovers":
        return json.dumps(leftovers.shuffle_report(args["letters"]))
    if fn == "strain":
        letters = anagrams.letters_only(args["letters"])
        return json.dumps(strained(letters, args["active"]))
    if fn == "check":
        name = anagrams.letters_only(args["name"])
        return json.dumps(sieve.verdict(name, letter_stats(), tuple(args["active"])) if name else None)
    if fn == "chef":
        found = chef.chefs_choice(args["name"], words())
        kind = [p for p in found if decency.NOT_ON_THE_PIER.isdisjoint(p.split())]
        return json.dumps({"phrases": kind, "hidden": len(found) - len(kind)})
    raise ValueError(f"Unknown call {fn!r}")
`;

type Shuffle = { letters: string; anagrams: string[]; hidden: number };
type Families = {
  words: number;
  families: number;
  in_families: number;
  longest: string[];
  top: string[][];
  hidden: number;
};

const $ = <T extends HTMLElement>(id: string) => document.getElementById(id) as T;
const input = $<HTMLInputElement>("word");
const pegs = $<HTMLOListElement>("pegs");
const feltFoot = $("felt-foot");
const status = $("status");
const specials = $<HTMLUListElement>("specials");
const menuLede = $("menu-lede");
const familyList = $<HTMLOListElement>("families");
const hiddenNote = $("hidden-note");

const python = new Python();
const calm = () => matchMedia("(prefers-reduced-motion: reduce)").matches;
let timer = 0;
let request = 0;
let original = ""; // the letters as the visitor typed them
let showing = ""; // the word on the board right now
let hiddenOnBoard = 0;

/** Peg letters (in a stable order of spans) for a word, one span per letter. */
function pegsFor(word: string) {
  return [...word].map((letter) => {
    const li = document.createElement("li");
    li.textContent = letter.toUpperCase();
    li.dataset.letter = letter;
    return li;
  });
}

function setBoard(word: string) {
  showing = word;
  pegs.style.setProperty("--n", String(Math.max(word.length, 1)));
  pegs.replaceChildren(...pegsFor(word));
}

/**
 * Re-peg the board as `target`, which uses the same letters. Each peg moves to its new groove:
 * we note where every letter sits, reorder the same elements, then animate each one from its
 * old spot to the new one (the FLIP technique: First, Last, Invert, Play).
 */
function repeg(target: string) {
  const current = [...pegs.children] as HTMLLIElement[];
  if (current.length !== target.length || calm()) {
    setBoard(target);
    return;
  }
  const first = new Map(current.map((li) => [li, li.getBoundingClientRect()]));
  const unused = [...current];
  const order = [...target].map((letter) => {
    const at = unused.findIndex((li) => li.dataset.letter === letter);
    return unused.splice(at, 1)[0];
  });
  pegs.replaceChildren(...order);
  showing = target;
  order.forEach((li, i) => {
    const before = first.get(li)!;
    const after = li.getBoundingClientRect();
    const dx = before.left - after.left;
    if (Math.abs(dx) < 1) return;
    li.animate(
      [
        { transform: `translate(${dx}px, 0)` },
        { transform: `translate(${dx * 0.5}px, -1.4em) rotate(${dx > 0 ? -8 : 8}deg)`, offset: 0.45 },
        { transform: "translate(0, 0)" },
      ],
      { duration: 620, delay: i * 45, easing: "cubic-bezier(0.3, 0.7, 0.3, 1)" },
    );
  });
}

function special(word: string, label: string, isHome = false) {
  const li = document.createElement("li");
  const button = document.createElement("button");
  button.type = "button";
  button.textContent = label;
  button.className = isHome ? "special is-home" : "special";
  button.setAttribute("aria-pressed", String(word === showing));
  button.addEventListener("click", () => {
    repeg(word);
    for (const other of specials.querySelectorAll("button")) {
      other.setAttribute("aria-pressed", String(other === button));
    }
    status.textContent = isHome ? `Back to ${original}.` : `${original.toUpperCase()} is now ${word.toUpperCase()}.`;
  });
  li.append(button);
  return li;
}

function show(result: Shuffle, asked: string) {
  original = result.letters;
  hiddenOnBoard = result.hidden;
  setBoard(original);
  const found = result.anagrams;
  feltFoot.textContent = found.length ? `${found.length} special${found.length === 1 ? "" : "s"}` : "";
  specials.replaceChildren(
    ...(found.length ? [special(original, `${original} (yours)`, true), ...found.map((w) => special(w, w))] : []),
  );
  const shown = asked.trim();
  if (!original) {
    status.textContent = "Type a name or a word to put it on the board.";
  } else if (original.length === 1) {
    status.textContent = "One letter can't shuffle. Give the waiter a few more.";
  } else if (found.length) {
    status.textContent = `${found.length === 1 ? "One word hides" : `${found.length} words hide`} in ${shown}. Tap one to re-peg the board.`;
  } else {
    status.textContent = `No specials today for ${shown}. Try a nickname, or a shorter word?`;
  }
  if (hiddenOnBoard) status.textContent += " (A rude one stays in the kitchen.)";
}

function schedule() {
  window.clearTimeout(timer);
  timer = window.setTimeout(() => void look(), 120);
}

async function look() {
  const mine = ++request; // ignore answers to older keystrokes
  try {
    const asked = input.value;
    const result = await python.call<Shuffle>("shuffle", { text: asked });
    if (mine === request) show(result, asked);
  } catch (error) {
    console.error(error);
    status.textContent = "The waiter dropped the letters. Try another word.";
  }
}

function order(word: string) {
  input.value = word;
  void look();
  $("board").scrollIntoView({ behavior: calm() ? "auto" : "smooth", block: "start" });
}

function renderFamilies(data: Families) {
  menuLede.replaceChildren(
    "Out of ",
    strong(data.words.toLocaleString()),
    " words, ",
    strong(data.in_families.toLocaleString()),
    " share their letters with another word, in ",
    strong(data.families.toLocaleString()),
    ` families. The longest pair is ${data.longest.join(" and ")}. Tap a family to put it on the board.`,
  );
  familyList.replaceChildren(
    ...data.top.map((family) => {
      const li = document.createElement("li");
      const button = document.createElement("button");
      button.type = "button";
      const size = document.createElement("span");
      size.className = "family-size";
      size.textContent = String(family.length);
      const names = document.createElement("span");
      names.className = "family-words";
      names.textContent = family.join(", ");
      button.append(size, names);
      button.setAttribute("aria-label", `${family.length} words: ${family.join(", ")}`);
      button.addEventListener("click", () => order(family[0]));
      li.append(button);
      return li;
    }),
  );
  hiddenNote.textContent = data.hidden
    ? `A few rude words stay in the dictionary, not on the board: ${data.hidden} of them are left off this menu.`
    : "";
}

function strong(text: string) {
  const node = document.createElement("strong");
  node.textContent = text;
  return node;
}

function pegTheSign() {
  const sign = $("sign-pegs");
  sign.replaceChildren(
    ...[...(sign.textContent ?? "")].map((char) => {
      const span = document.createElement("span");
      span.className = char === " " ? "gap" : "peg";
      span.textContent = char;
      return span;
    }),
  );
}

async function start() {
  pegTheSign();
  setBoard("welcome"); // something friendly on the board while Python loads
  python.onProgress = (stage) => (status.textContent = `${stage}…`);
  try {
    const words = await fetch(wordListUrl).then((response) => {
      if (!response.ok) throw new Error(`Word list: HTTP ${response.status}`);
      return response.text();
    });
    await python.init("shuffle_cafe", { ...commonSources, ...shuffleCafeSources, "2of4brif.txt": words }, BRIDGE);
    status.textContent = "Sorting the dictionary into families…";
    renderFamilies(await python.call<Families>("families", { count: 8 }));
  } catch (error) {
    console.error(error);
    status.textContent = "The café couldn't open. Check your connection and reload the page.";
    menuLede.textContent = "";
    return;
  }
  input.addEventListener("input", schedule);
  input.disabled = false;
  for (const button of document.querySelectorAll<HTMLButtonElement>(".regulars button")) {
    button.addEventListener("click", () => order(button.dataset.word ?? ""));
  }
  input.value = "Daniel";
  await look();
  await startPhrases(python);
  await startChef(python);
  await startSieve(python);
}

void start();
