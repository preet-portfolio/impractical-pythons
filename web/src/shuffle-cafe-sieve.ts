// The kitchen sieve: Python makes every ordering of up to nine letters and strains them through
// three sieves; the page shows the counts dropping, lets the visitor pull a sieve out to see
// what it was catching, serves the best survivor as a fresh new word, and explains in plain
// words why any word they type would (or wouldn't) get through.
import type { Python } from "./py/python";

type Stage = { sieve: string; on: boolean; left: number };
type Pair = { pair: string; share: number; rare: boolean };
type Strained = {
  letters: string;
  too_many?: boolean;
  start: number;
  stages: Stage[];
  survivors: string[];
  by_letter: Record<string, number>;
  hidden: number;
  pairs: Pair[];
};
type Verdict = { name: string; passed: boolean; caught_by: string | null; reason: string } | null;

const SHOWN = 60; // survivors shown at once
const SIEVE_NAMES: Record<string, string> = {
  shape: "the shape sieve",
  triples: "the three-letter sieve",
  pairs: "the two-letter sieve",
};

const $ = <T extends HTMLElement>(id: string) => document.getElementById(id) as T;
const lettersInput = $<HTMLInputElement>("sieve-letters");
const pour = $("sieve-start");
const colanders = [...document.querySelectorAll<HTMLButtonElement>(".colander")];
const invention = $("invention");
const inventionName = $("invention-name");
const inventionFrom = $("invention-from");
const inventionCopy = $<HTMLButtonElement>("invention-copy");
const inventionPeg = $<HTMLButtonElement>("invention-peg");
const firstLetters = $("first-letters");
const dripList = $<HTMLUListElement>("drip-list");
const dripNote = $("drip-note");
const checkInput = $<HTMLInputElement>("check-name");
const checkResult = $("check-result");
const pairFact = $("pair-fact");
const pairTable = $<HTMLTableElement>("pair-table");

let python: Python;
let active = new Set(["shape", "triples", "pairs"]);
let report: Strained | null = null;
let letterFilter = ""; // "" shows every first letter
let picked = "";
let tray = ""; // letters left in the phrase builder's tray, if any
let request = 0;
let checkRequest = 0;
let timer = 0;
let checkTimer = 0;
const calm = () => matchMedia("(prefers-reduced-motion: reduce)").matches;
const spaced = (letters: string) => letters.toUpperCase().split("").join("-");
const capital = (word: string) => word.charAt(0).toUpperCase() + word.slice(1);

/** Count a number up or down to its new value, like a till. Instant with reduced motion. */
function tick(node: HTMLElement, to: number, delay: number) {
  const from = Number(node.dataset.value ?? to);
  node.dataset.value = String(to);
  if (calm() || from === to) {
    node.textContent = to.toLocaleString();
    return;
  }
  const started = performance.now() + delay;
  const step = (now: number) => {
    const t = Math.min(Math.max((now - started) / 700, 0), 1);
    const eased = 1 - (1 - t) ** 3;
    node.textContent = Math.round(from + (to - from) * eased).toLocaleString();
    if (t < 1) requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
}

function renderColanders(result: Strained) {
  pour.textContent = `${result.start.toLocaleString()} ways to order ${spaced(result.letters)}. Into the sieves they go…`;
  const scale = Math.log10(result.start + 1) || 1;
  result.stages.forEach((stage, i) => {
    const colander = colanders[i];
    colander.setAttribute("aria-pressed", String(stage.on));
    colander.classList.toggle("is-off", !stage.on);
    tick(colander.querySelector<HTMLElement>(".colander-count")!, stage.left, i * 220);
    // The pile under each sieve shrinks with what's left (on a log scale, or it'd vanish).
    colander.style.setProperty("--pile", String(Math.log10(stage.left + 1) / scale));
  });
}

function renderInvention() {
  invention.hidden = !picked;
  if (!picked || !report) return;
  inventionName.textContent = capital(picked);
  inventionFrom.textContent = `Strained from ${spaced(report.letters)}, one of ${report.survivors.length.toLocaleString()} that got through.`;
  inventionPeg.hidden = !tray || tray !== report.letters;
}

function pick(word: string) {
  picked = word;
  renderInvention();
  for (const b of dripList.querySelectorAll("button")) b.setAttribute("aria-pressed", String(b.textContent === word));
}

function renderDrips() {
  if (!report) return;
  const all = report.survivors;
  const matches = letterFilter ? all.filter((w) => w.startsWith(letterFilter)) : all;
  dripList.replaceChildren(
    ...matches.slice(0, SHOWN).map((word) => {
      const li = document.createElement("li");
      const b = document.createElement("button");
      b.type = "button";
      b.textContent = word;
      b.setAttribute("aria-pressed", String(word === picked));
      b.addEventListener("click", () => pick(word));
      li.append(b);
      return li;
    }),
  );
  const hidden = report.hidden ? ` (${report.hidden} rude-sounding ${report.hidden === 1 ? "one stays" : "ones stay"} in the kitchen.)` : "";
  if (!all.length) {
    const off = report.stages.filter((s) => s.on).length;
    dripNote.textContent = off
      ? "Nothing got through! Take a sieve out, or try different letters."
      : "Nothing to strain.";
  } else if (matches.length > SHOWN) {
    const more = letterFilter ? ` starting with ${letterFilter.toUpperCase()}` : ". Pick a first letter to see others";
    dripNote.textContent = `Showing the ${SHOWN} most English-sounding of ${matches.length.toLocaleString()}${more}.${hidden}`;
  } else {
    dripNote.textContent = `${matches.length.toLocaleString()} got through${letterFilter ? ` starting with ${letterFilter.toUpperCase()}` : ""}.${hidden}`;
  }
}

function renderFirstLetters() {
  if (!report) return;
  const chip = (letter: string, label: string) => {
    const b = document.createElement("button");
    b.type = "button";
    b.className = "letter-chip";
    b.textContent = label;
    b.setAttribute("aria-pressed", String(letter === letterFilter));
    b.addEventListener("click", () => {
      letterFilter = letter;
      renderFirstLetters();
      renderDrips();
    });
    return b;
  };
  firstLetters.replaceChildren(
    chip("", `All ${report.survivors.length.toLocaleString()}`),
    ...Object.entries(report.by_letter).map(([letter, count]) => chip(letter, `${letter.toUpperCase()} ${count}`)),
  );
}

/** The pastry-case board of letter pairs: rows are the first letter, columns the second. */
function renderPairs(pairs: Pair[], letters: string) {
  const unique = [...new Set(letters)].sort();
  const byPair = new Map(pairs.map((p) => [p.pair, p]));
  const top = Math.max(...pairs.map((p) => p.share), 1);
  const head = document.createElement("tr");
  head.append(document.createElement("th"));
  for (const second of unique) {
    const th = document.createElement("th");
    th.scope = "col";
    th.textContent = second.toUpperCase();
    head.append(th);
  }
  const rows = unique.map((first) => {
    const tr = document.createElement("tr");
    const th = document.createElement("th");
    th.scope = "row";
    th.textContent = first.toUpperCase();
    tr.append(th);
    for (const second of unique) {
      const td = document.createElement("td");
      const pair = byPair.get(first + second);
      if (pair) {
        td.textContent = pair.share < 0.05 ? "0" : pair.share.toFixed(1);
        td.style.setProperty("--heat", String(pair.share / top));
        td.classList.toggle("is-rare", pair.rare);
        td.title = `${first}${second}: ${pair.share.toFixed(2)}%${pair.rare ? ", caught by the two-letter sieve" : ""}`;
      } else {
        td.className = "is-none";
        td.title = `Only one ${first.toUpperCase()}, so it can't pair with itself`;
      }
      tr.append(td);
    }
    return tr;
  });
  pairTable.replaceChildren(head, ...rows);
  const rarest = [...pairs].sort((a, b) => a.share - b.share)[0];
  const commonest = [...pairs].sort((a, b) => b.share - a.share)[0];
  pairFact.textContent =
    rarest && commonest
      ? `Of the pairs these letters make, English loves "${commonest.pair}" most and "${rarest.pair}" least.`
      : "";
}

async function strainNow() {
  const mine = ++request;
  const letters = lettersInput.value;
  const clean = letters.toLowerCase().replace(/[^a-z]/g, "");
  if (clean.length < 3) {
    pour.textContent = "Give the kitchen at least three letters.";
    return;
  }
  if (clean.length > 9) {
    pour.textContent = `${clean.length} letters make millions of orderings: too many for one kitchen. Nine letters at most, please.`;
    return;
  }
  pour.textContent = `Laying out every order of ${spaced(clean)}…`;
  try {
    const result = await python.call<Strained>("strain", { letters, active: [...active] });
    if (mine !== request || result.too_many) return;
    report = result;
    if (!result.by_letter[letterFilter]) letterFilter = "";
    picked = result.survivors[0] ?? "";
    renderColanders(result);
    renderFirstLetters();
    renderDrips();
    renderInvention();
    renderPairs(result.pairs, result.letters);
  } catch (error) {
    console.error(error);
    pour.textContent = "The sieve got clogged. Try those letters again.";
  }
}

async function checkNow() {
  const mine = ++checkRequest;
  try {
    const result = await python.call<Verdict>("check", { name: checkInput.value, active: [...active] });
    if (mine !== checkRequest) return;
    if (!result) {
      checkResult.textContent = "Type a made-up word (or a real one) to pour it through.";
      checkResult.className = "check-result";
    } else if (result.passed) {
      checkResult.textContent = `${capital(result.name)} gets through every sieve that's in. It sounds like it could be English.`;
      checkResult.className = "check-result is-pass";
    } else {
      checkResult.textContent = `${capital(result.name)} is caught by ${SIEVE_NAMES[result.caught_by ?? ""]}. ${result.reason}`;
      checkResult.className = "check-result is-caught";
    }
  } catch (error) {
    console.error(error);
    checkResult.textContent = "That one jammed the sieve. Try another word.";
  }
}

function strainSoon() {
  window.clearTimeout(timer);
  timer = window.setTimeout(() => void strainNow(), 250);
}

export async function startSieve(py: Python) {
  python = py;
  lettersInput.disabled = checkInput.disabled = false;
  lettersInput.addEventListener("input", strainSoon);
  checkInput.addEventListener("input", () => {
    window.clearTimeout(checkTimer);
    checkTimer = window.setTimeout(() => void checkNow(), 200);
  });
  for (const button of document.querySelectorAll<HTMLButtonElement>("#sieve .regulars button")) {
    button.addEventListener("click", () => {
      lettersInput.value = button.dataset.letters ?? "";
      void strainNow();
    });
  }
  for (const colander of colanders) {
    colander.addEventListener("click", () => {
      const sieve = colander.dataset.sieve ?? "";
      active = new Set(active); // a fresh set, so a slow answer for the old one can't mix in
      if (active.has(sieve)) active.delete(sieve);
      else active.add(sieve);
      void strainNow();
      if (checkInput.value) void checkNow();
    });
  }
  inventionCopy.addEventListener("click", async () => {
    if (!picked) return;
    const text = `${capital(picked)}: a brand-new word, strained from ${spaced(report?.letters ?? picked)} at the Shuffle Café.`;
    try {
      await navigator.clipboard.writeText(text);
      inventionFrom.textContent = "Copied. Go and name something with it!";
    } catch {
      inventionFrom.textContent = `Copy this: ${text}`;
    }
  });
  inventionPeg.addEventListener("click", () => {
    if (picked) document.dispatchEvent(new CustomEvent("cafe:peg", { detail: picked }));
  });
  document.addEventListener("cafe:tray", (event) => {
    tray = (event as CustomEvent<string>).detail;
    renderInvention();
  });
  document.addEventListener("cafe:strain", (event) => {
    lettersInput.value = (event as CustomEvent<string>).detail;
    $("sieve").scrollIntoView({ behavior: calm() ? "auto" : "smooth", block: "start" });
    void strainNow();
  });
  lettersInput.value = "teacakes";
  checkInput.value = "doughnut"; // a real word that gets caught: the sieve isn't perfect
  await strainNow();
  await checkNow();
}
