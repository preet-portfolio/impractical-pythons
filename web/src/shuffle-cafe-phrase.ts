// The phrase builder: a second board where a name's letters wait in a tray, and the visitor
// pegs words onto the board one at a time until every letter is used. Python decides what
// fits; the page only remembers which words were chosen.
import type { Python } from "./py/python";

type PhraseStatus = {
  name: string;
  phrase: string;
  left: string;
  done: boolean;
  options: string[];
};

const SHOWN = 48; // option slips shown at once

const $ = <T extends HTMLElement>(id: string) => document.getElementById(id) as T;
const nameInput = $<HTMLInputElement>("phrase-name");
const board = $<HTMLOListElement>("phrase-pegs");
const head = $("phrase-head");
const tray = $<HTMLOListElement>("tray");
const options = $<HTMLUListElement>("phrase-options");
const find = $<HTMLInputElement>("phrase-find");
const note = $("phrase-note");
const status = $("phrase-status");
const undo = $<HTMLButtonElement>("phrase-undo");
const restart = $<HTMLButtonElement>("phrase-restart");
const copy = $<HTMLButtonElement>("phrase-copy");
const slips = $("phrase-slips");

let python: Python;
let chosen: string[] = [];
let current: PhraseStatus | null = null;
let request = 0;
let timer = 0;
const calm = () => matchMedia("(prefers-reduced-motion: reduce)").matches;

function peg(char: string, extra = "") {
  const li = document.createElement("li");
  li.textContent = char.toUpperCase();
  li.dataset.letter = char;
  li.className = char === " " ? "gap" : extra;
  return li;
}

/** Where each loose letter sits in the tray right now, so new pegs can fly up from there. */
function trayPositions() {
  const spots = new Map<string, DOMRect[]>();
  for (const li of tray.children as HTMLCollectionOf<HTMLLIElement>) {
    const letter = li.dataset.letter ?? "";
    spots.set(letter, [...(spots.get(letter) ?? []), li.getBoundingClientRect()]);
  }
  return spots;
}

function render(next: PhraseStatus, added: string | null) {
  const from = trayPositions();
  current = next;
  const words = next.phrase ? next.phrase.split(" ") : [];
  const letters = words.join(" ");
  board.style.setProperty("--n", String(Math.max(letters.length, 6)));
  board.replaceChildren(
    ...words.flatMap((word, w) => {
      const isNew = added !== null && w === words.length - 1;
      const pegs = [...word].map((char) => peg(char, isNew ? "is-new" : ""));
      return w ? [peg(" "), ...pegs] : pegs;
    }),
  );
  tray.replaceChildren(...[...next.left].map((char) => peg(char)));
  head.textContent = next.done ? "Order up!" : words.length ? "Your phrase" : "Pick a word below";

  // Fly each new peg up from the tray spot its letter just left.
  if (added && !calm()) {
    board.querySelectorAll<HTMLLIElement>("li.is-new").forEach((li, i) => {
      const start = from.get(li.dataset.letter ?? "")?.shift();
      if (!start) return;
      const end = li.getBoundingClientRect();
      li.animate(
        [
          { transform: `translate(${start.left - end.left}px, ${start.top - end.top}px) scale(0.6)` },
          { transform: "translate(0, 0) scale(1)" },
        ],
        { duration: 520, delay: i * 50, easing: "cubic-bezier(0.25, 0.9, 0.35, 1.15)", fill: "backwards" },
      );
    });
  }

  undo.disabled = chosen.length === 0;
  restart.disabled = chosen.length === 0;
  copy.hidden = !next.done;
  slips.hidden = next.done; // nothing left to pick
  if (next.done) {
    status.textContent = `${next.name} = ${next.phrase}. Every letter used!`;
  } else if (!next.left) {
    status.textContent = "Type a name to fill the tray.";
  } else if (next.options.length === 0) {
    status.textContent = `No words fit ${next.left.toUpperCase()}. Undo a word and try another.`;
  } else {
    status.textContent = `${next.left.length} letters left in the tray.`;
  }
  renderOptions();
}

function renderOptions() {
  const all = current?.options ?? [];
  const needle = find.value.trim().toLowerCase().replace(/[^a-z]/g, "");
  const matches = needle ? all.filter((word) => word.includes(needle)) : all;
  options.replaceChildren(
    ...matches.slice(0, SHOWN).map((word) => {
      const li = document.createElement("li");
      const button = document.createElement("button");
      button.type = "button";
      button.className = "special";
      button.textContent = word;
      button.addEventListener("click", () => void choose(word));
      li.append(button);
      return li;
    }),
  );
  if (!all.length) note.textContent = "";
  else if (!matches.length) note.textContent = `No words with "${needle}" fit. Try fewer letters.`;
  else if (matches.length > SHOWN) note.textContent = `Showing the ${SHOWN} longest of ${matches.length} words that fit.`;
  else note.textContent = `${matches.length} ${matches.length === 1 ? "word fits" : "words fit"}.`;
}

async function refresh(added: string | null = null) {
  const mine = ++request;
  try {
    const next = await python.call<PhraseStatus | null>("phrase", { name: nameInput.value, chosen });
    if (mine !== request) return;
    if (next === null) {
      chosen = chosen.slice(0, -1); // shouldn't happen: every option fits
      return;
    }
    render(next, added);
  } catch (error) {
    console.error(error);
    status.textContent = "The tray slipped. Try that again.";
  }
}

async function choose(word: string) {
  chosen = [...chosen, word];
  find.value = "";
  await refresh(word);
}

function newName(name: string) {
  nameInput.value = name;
  chosen = [];
  find.value = "";
  void refresh();
}

export async function startPhrases(py: Python) {
  python = py;
  nameInput.disabled = find.disabled = false;
  nameInput.addEventListener("input", () => {
    window.clearTimeout(timer);
    chosen = [];
    timer = window.setTimeout(() => void refresh(), 150);
  });
  find.addEventListener("input", renderOptions);
  undo.addEventListener("click", () => {
    chosen = chosen.slice(0, -1);
    void refresh();
  });
  restart.addEventListener("click", () => {
    chosen = [];
    void refresh();
  });
  copy.addEventListener("click", async () => {
    if (!current) return;
    try {
      await navigator.clipboard.writeText(`${current.name} = ${current.phrase}`);
      status.textContent = "Copied. Send it to someone with that name!";
    } catch {
      status.textContent = `Copy this: ${current.name} = ${current.phrase}`;
    }
  });
  for (const button of document.querySelectorAll<HTMLButtonElement>(".phrase-regulars button")) {
    button.addEventListener("click", () => newName(button.dataset.name ?? ""));
  }
  newName("Ice Cream Van");
}
