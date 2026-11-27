import "./styles.css";
import { Python } from "./py/python";
import { aliasSlotsSources } from "./py/sources";

// Shapes of the data Python sends back (see slots.catalogue and slots.Spin).
type Prize = "jackpot" | "rhyme" | "pair" | null;
type Theme = {
  key: string;
  title: string;
  blurb: string;
  reel_names: string[];
  reels: string[][];
  combinations: number;
  odds: Record<"jackpot" | "rhyme" | "pair", number>;
};
type Spin = { theme: string; indices: number[]; words: string[]; name: string; prize: Prize; code: string };
type DecodeResult = Spin | { error: string };

const COPIES = 7; // each strip repeats its words so a spin can travel several loops
const HISTORY_KEY = "alias-slots-history";
const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

const $ = <T extends HTMLElement>(id: string) => document.getElementById(id) as T;
const els = {
  marquee: $("marquee"),
  themes: $<HTMLFieldSetElement>("themes"),
  blurb: $("blurb"),
  reels: $("reels"),
  lever: $<HTMLButtonElement>("lever"),
  spin: $<HTMLButtonElement>("spin"),
  odds: $("odds"),
  ticket: $("ticket"),
  ticketPrize: $("ticket-prize"),
  ticketName: $("ticket-name"),
  ticketEmpty: $("ticket-empty"),
  copyName: $<HTMLButtonElement>("copy-name"),
  copyLink: $<HTMLButtonElement>("copy-link"),
  copied: $("copied"),
  announce: $("announce"),
  history: $<HTMLOListElement>("history"),
  historyTitle: $("history-title"),
};

const python = new Python();
let themes: Theme[] = [];
let theme: Theme;
let positions: number[] = []; // where each reel currently rests
let current: Spin | null = null; // the last alias printed for this theme
const held = new Set<number>();
let spinning = false;
let history: Spin[] = [];

// ---- reels --------------------------------------------------------------------------

function strip(reel: number) {
  return els.reels.querySelector<HTMLElement>(`[data-reel="${reel}"] .strip`)!;
}

/** Put a reel's strip so row `row` (counting through all copies) sits in the window's centre. */
function place(reel: number, row: number, animate: boolean, duration = 0) {
  const el = strip(reel);
  el.style.transition = animate ? `transform ${duration}ms cubic-bezier(.17,.67,.21,1.04)` : "none";
  el.style.transform = `translateY(calc((0.5 - ${row}) * var(--row)))`;
}

function buildReels() {
  els.reels.replaceChildren();
  theme.reels.forEach((words, i) => {
    const reel = document.createElement("div");
    reel.className = "reel";
    reel.dataset.reel = String(i);

    const label = document.createElement("p");
    label.className = "reel-name";
    label.id = `reel-name-${i}`;
    label.textContent = theme.reel_names[i];

    const win = document.createElement("div");
    win.className = "window";
    win.setAttribute("aria-hidden", "true");
    const list = document.createElement("ul");
    list.className = "strip";
    for (let copy = 0; copy < COPIES; copy++) {
      for (const word of words) {
        const li = document.createElement("li");
        li.textContent = word;
        list.append(li);
      }
    }
    win.append(list);

    const hold = document.createElement("button");
    hold.type = "button";
    hold.className = "hold";
    hold.textContent = "Hold";
    hold.setAttribute("aria-pressed", "false");
    hold.setAttribute("aria-describedby", label.id);
    hold.disabled = true;
    hold.addEventListener("click", () => toggleHold(i));

    reel.append(label, win, hold);
    els.reels.append(reel);
    place(i, positions[i], false);
  });
}

function toggleHold(reel: number) {
  if (!current || spinning) return;
  if (held.has(reel)) held.delete(reel);
  else held.add(reel);
  syncHolds();
}

function syncHolds() {
  els.reels.querySelectorAll<HTMLButtonElement>(".hold").forEach((button, i) => {
    const on = held.has(i);
    button.setAttribute("aria-pressed", String(on));
    button.textContent = on ? "Held" : "Hold";
    button.disabled = !current || spinning;
    button.closest(".reel")!.classList.toggle("is-held", on);
  });
}

/** Spin every unheld reel to its new stop, left to right, each one landing a beat later. */
function animateTo(indices: number[]): Promise<void> {
  const moves = indices.map((target, i) => {
    if (held.has(i)) return Promise.resolve();
    const length = theme.reels[i].length;
    const from = positions[i];
    positions[i] = target;
    if (reduceMotion.matches) {
      place(i, target, false);
      return Promise.resolve();
    }
    const loops = 2 + i; // later reels travel further, so they stop one after another
    const duration = 1100 + i * 450;
    place(i, from, false);
    strip(i).getBoundingClientRect(); // commit the jump before animating
    place(i, loops * length + target, true, duration);
    return new Promise<void>((resolve) => {
      const done = () => {
        place(i, target, false); // snap back to the first copy, invisibly
        resolve();
      };
      strip(i).addEventListener("transitionend", done, { once: true });
      window.setTimeout(done, duration + 200); // in case transitionend never fires
    });
  });
  return Promise.all(moves).then(() => undefined);
}

// ---- spinning -----------------------------------------------------------------------

async function pull() {
  if (spinning || !theme) return;
  spinning = true;
  setBusy(true);
  els.lever.classList.add("pulled");
  window.setTimeout(() => els.lever.classList.remove("pulled"), 450);
  els.marquee.classList.remove("win", "glow");
  try {
    const locked = Object.fromEntries([...held].map((i) => [i, positions[i]]));
    const result = await python.call<Spin>("spin", { theme: theme.key, locked });
    await animateTo(result.indices);
    showTicket(result, true);
  } catch (error) {
    failed(error);
  } finally {
    spinning = false;
    setBusy(false);
  }
}

function setBusy(busy: boolean) {
  els.spin.disabled = busy;
  els.lever.disabled = busy;
  els.themes.disabled = busy;
  syncHolds();
}

const PRIZE_TEXT: Record<Exclude<Prize, null>, (s: Spin) => string> = {
  jackpot: (s) => `Jackpot! Every reel starts with ${firstLetter(s.words[0])}.`,
  rhyme: () => "Rhyme bonus!",
  pair: () => "A pair. Two reels share a first letter.",
};

function firstLetter(word: string) {
  const skip = new Set(["the", "of", "a", "an"]);
  const part = word.split(" ").find((w) => !skip.has(w.toLowerCase())) ?? word;
  return part[0].toUpperCase();
}

function showTicket(spin: Spin, fresh: boolean) {
  current = spin;
  els.ticket.hidden = false;
  els.ticketEmpty.hidden = true;
  els.ticketName.textContent = spin.name;
  els.ticketPrize.textContent = spin.prize ? PRIZE_TEXT[spin.prize](spin) : "No prize, but what a name.";
  els.ticket.dataset.prize = spin.prize ?? "none";
  history_replace(spin.code);

  if (fresh) {
    // Re-trigger the print animation on every new ticket.
    els.ticket.classList.remove("printing");
    void els.ticket.offsetWidth;
    els.ticket.classList.add("printing");
    if (spin.prize === "jackpot") els.marquee.classList.add("win");
    else if (spin.prize) els.marquee.classList.add("glow");
    els.announce.textContent = `Your alias is ${spin.name}. ${els.ticketPrize.textContent}`;
    remember(spin);
  }
  syncHolds();
}

function history_replace(code: string) {
  const url = new URL(window.location.href);
  url.searchParams.set("n", code);
  window.history.replaceState(null, "", url);
}

// ---- history ------------------------------------------------------------------------

function remember(spin: Spin) {
  history = [spin, ...history.filter((h) => h.code !== spin.code)].slice(0, 10);
  try {
    localStorage.setItem(HISTORY_KEY, JSON.stringify(history.map((h) => h.code)));
  } catch {
    // Private browsing can refuse storage; the list still works for this visit.
  }
  renderHistory();
}

function renderHistory() {
  const earlier = history.slice(1);
  els.historyTitle.hidden = earlier.length === 0;
  els.history.replaceChildren(
    ...earlier.map((spin) => {
      const li = document.createElement("li");
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = spin.name;
      button.addEventListener("click", () => restore(spin));
      li.append(button);
      return li;
    }),
  );
}

async function loadHistory() {
  let codes: string[] = [];
  try {
    codes = JSON.parse(localStorage.getItem(HISTORY_KEY) ?? "[]");
  } catch {
    codes = [];
  }
  const found = await Promise.all(codes.slice(0, 10).map((code) => python.call<DecodeResult>("decode", { code })));
  // Word lists may change between visits; a code that no longer decodes is dropped.
  history = found.filter((r): r is Spin => !("error" in r));
}

// ---- themes and restoring -----------------------------------------------------------

function selectTheme(key: string, rest?: number[]) {
  theme = themes.find((t) => t.key === key) ?? themes[0];
  held.clear();
  current = null;
  positions = rest ?? theme.reels.map((reel) => Math.floor(Math.random() * reel.length));
  els.blurb.textContent = theme.blurb;
  const radio = els.themes.querySelector<HTMLInputElement>(`input[value="${theme.key}"]`);
  if (radio) radio.checked = true;
  const each = (count: number) =>
    count ? `1 in ${Math.round(theme.combinations / count).toLocaleString()}` : "never";
  els.odds.textContent =
    `${theme.combinations.toLocaleString()} possible aliases. ` +
    `Jackpot ${each(theme.odds.jackpot)}, rhyme ${each(theme.odds.rhyme)}, pair ${each(theme.odds.pair)}.`;
  buildReels();
  syncHolds();
}

function restore(spin: Spin) {
  if (spinning) return;
  selectTheme(spin.theme, [...spin.indices]);
  els.marquee.classList.remove("win", "glow");
  showTicket(spin, false);
  history = [spin, ...history.filter((h) => h.code !== spin.code)];
  renderHistory();
}

function buildThemePicker() {
  for (const t of themes) {
    const label = document.createElement("label");
    label.className = "theme";
    const input = document.createElement("input");
    input.type = "radio";
    input.name = "theme";
    input.value = t.key;
    input.addEventListener("change", () => selectTheme(t.key));
    const text = document.createElement("span");
    text.textContent = t.title;
    label.append(input, text);
    els.themes.append(label);
  }
}

// ---- copying, keys and start-up -----------------------------------------------------

async function copy(text: string, message: string) {
  try {
    await navigator.clipboard.writeText(text);
    els.copied.textContent = message;
  } catch {
    els.copied.textContent = "Copying isn't allowed here. Select the text instead.";
  }
  window.setTimeout(() => (els.copied.textContent = ""), 2500);
}

function failed(error: unknown) {
  console.error(error);
  els.spin.textContent = "Python didn't load";
  els.ticketEmpty.hidden = false;
  els.ticketEmpty.textContent =
    "Python couldn't start in this browser. Check your connection and reload the page.";
}

function wireUp() {
  els.spin.addEventListener("click", pull);
  els.lever.addEventListener("click", pull);
  els.copyName.addEventListener("click", () => current && copy(current.name, "Copied the name."));
  els.copyLink.addEventListener("click", () => current && copy(window.location.href, "Copied the link."));
  document.addEventListener("keydown", (event) => {
    if (event.metaKey || event.ctrlKey || event.altKey) return;
    const target = event.target as HTMLElement;
    if (target.closest("input, textarea, select, button, a")) return; // let controls handle their own keys
    if (event.key === " ") {
      event.preventDefault();
      void pull();
    } else if (["1", "2", "3"].includes(event.key)) {
      toggleHold(Number(event.key) - 1);
    }
  });
}

async function start() {
  wireUp();
  python.onProgress = (stage) => (els.spin.textContent = `${stage}…`);
  try {
    await python.init(aliasSlotsSources);
    themes = await python.call<Theme[]>("catalogue");
    buildThemePicker();
    await loadHistory();

    const code = new URLSearchParams(window.location.search).get("n");
    const shared = code ? await python.call<DecodeResult>("decode", { code }) : null;
    if (shared && !("error" in shared)) {
      restore(shared);
    } else {
      selectTheme(themes[0].key);
      if (shared) {
        els.ticketEmpty.textContent = "That link's alias isn't on these reels any more. Pull the lever for a new one.";
      }
      renderHistory();
    }
    els.themes.disabled = false;
    els.spin.disabled = false;
    els.lever.disabled = false;
    els.spin.textContent = "Pull the lever";
  } catch (error) {
    failed(error);
  }
}

void start();
