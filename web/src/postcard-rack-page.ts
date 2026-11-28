import "./styles.css";
import "./postcard-rack.css";
import { Python } from "./py/python";
import { commonSources, postcardRackSources } from "./py/sources";
// The dictionary ships as its own file and is fetched at start: every look needs it.
import wordListUrl from "../../projects/common/data/2of4brif.txt?url";

// Python side of the page: called by the worker as _bridge(fn, args_json) -> JSON.
// The page never finds a letter itself: it asks Python where the secret is.
const BRIDGE = `
import json
from datetime import date
from pathlib import Path

import decency
import null_finder
import null_writer
import postcard_themes
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
            "rules": {rule: null_finder.describe(rule, 1) for rule in null_finder.RULES},
            "themes": [{key: theme[key] for key in ("id", "name", "place", "scene")}
                       for theme in postcard_themes.THEMES]}

def trusted(args):
    """Desk cards were written on one of the writer's settings: short words count there."""
    return null_writer.WRITERS_SETTINGS if args.get("desk") else frozenset()

def look(args):
    text, rule, offset = args["text"], args["rule"], args["offset"]
    positions = null_finder.picked_positions(text, rule, offset)
    letters = "".join(text[i] for i in positions).lower()
    short_ok = (rule, offset) in trusted(args)
    reading = null_finder.read_reading(letters, words(), short_ok) if letters else {
        "words": [], "coverage": 0, "word_length": 0, "reads": False}
    return {"positions": positions, "letters": letters,
            "setting": null_finder.describe(rule, offset)} | reading

def scan(args):
    return null_finder.scan(args["text"], words(), trusted=trusted(args))

def nans_words(position):
    """Nan's word bag, grouped by the letter at each position: built once each."""
    key = ("groups", position)
    if key not in _cache:
        _cache[key] = null_writer.words_by_letter(words(), position)
    return _cache[key]

def where(text):
    """The place and scene for a desk card: its theme's, or Nan's club for a list."""
    theme = null_writer.theme_of(text)
    if theme:
        return {"place": theme["place"], "scene": theme["scene"]}
    return {"place": "Nan's Scrabble Club", "scene": "club"}

def posted(text, letters, args):
    """A finished card, ready for the desk and packed for its link."""
    to = null_writer.clean_name(args["to"], "you")
    sender = null_writer.clean_name(args["sender"], "a friend")
    return {"text": text, "to": to, "sender": sender, "letters": letters,
            "token": null_writer.pack_card(text, to, sender)} | where(text)

def write(args):
    position = args["position"]
    try:
        letters = null_writer.check_note(args["note"])
        chosen = null_writer.choose_words(letters, nans_words(position), position, args["seed"])
    except null_writer.NoteProblem as problem:
        return {"problem": str(problem)}
    return posted(null_writer.write_card(chosen), letters, args)

def story(args):
    """A proper postcard from one of the themes."""
    try:
        text = null_writer.write_story(args["note"], args["theme"], args["position"], args["seed"])
    except null_writer.NoteProblem as problem:
        return {"problem": str(problem)}
    return posted(text, null_writer.note_letters(args["note"]), args)

def unpack(args):
    try:
        card = null_writer.unpack_card(args["token"])
    except null_writer.NoteProblem as problem:
        return {"problem": str(problem)}
    return card | where(card["text"])

CALLS = {"rack": rack, "look": look, "scan": scan, "write": write, "story": story,
         "unpack": unpack}

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
type Theme = { id: string; name: string; place: string; scene: string };
type Rack = { cards: Card[]; today: string; number: number; rules: Record<string, string>; themes: Theme[] };
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
type Place = { place: string; scene: string };
type Written = { text: string; to: string; sender: string; letters: string; token: string } & Place & { problem?: string };
type Received = { text: string; to: string; sender: string } & Place & { problem?: string };

const $ = <T extends HTMLElement>(id: string) => document.getElementById(id) as T;
const python = new Python();
const calm = () => matchMedia("(prefers-reduced-motion: reduce)").matches;

const SHORTEST = 6; // null_finder.SHORTEST: fewer letters than this never count as a note
const OWN = "own"; // the blank card for the visitor's own text
const WRITTEN = "written"; // the card the visitor just wrote
const RECEIVED = "received"; // a card that arrived in a link
const ORDINAL: Record<number, string> = { 2: "2nd", 3: "3rd", 4: "4th" };
const LONGEST_LIST = 40; // null_writer.LONGEST_NOTE
const LONGEST_STORY = 16; // null_writer.LONGEST_STORY_NOTE

const cardText = $("card-text");
const cardOwn = $<HTMLTextAreaElement>("card-own");
const status = $("status");
const foundStamp = $("found-stamp");

let cards: Card[] = [];
let extras: Card[] = []; // the written and received cards: on the desk, not on the rack
let token = ""; // the written card, packed for its link
let seed = 0;
let todayId = "";
let current: Card | null = null;
let request = 0;
let revealed = false;

const text = () => (current ? current.text : cardOwn.value);
/** Whether the card came from the writing desk (written here, or arrived in a link). */
const onDesk = () => current?.id === WRITTEN || current?.id === RECEIVED;
/** The sender, ready to start a sentence ("a friend" becomes "Your friend"). */
const who = (card: Card) => (card.sender === "a friend" ? "Your friend" : card.sender);
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

function stamp(show: boolean) {
  foundStamp.hidden = !show;
  foundStamp.classList.remove("is-landing");
  if (show && !calm()) {
    void foundStamp.offsetWidth; // restart the animation
    foundStamp.classList.add("is-landing");
  }
}

const MOSTLY_WORDS = 0.6; // on a card from a friend, this much real words is worth showing

/** Where the secret is, if there is one: the card's own answer, or Python's best guess. */
async function findSecret(): Promise<{ rule: string; offset: number; words: string } | null> {
  if (current && current.id !== RECEIVED) {
    return current.rule ? { rule: current.rule, offset: current.offset, words: current.note } : null;
  }
  // A card from a friend, or the visitor's own words: try every way of hiding and keep the best.
  const readings = await python.call<Reading[]>("scan", { text: text(), desk: onDesk() });
  const best = readings[0];
  if (!best) return null;
  const friend = current?.id === RECEIVED && best.coverage >= MOSTLY_WORDS;
  return best.reads || friend ? { rule: best.rule, offset: best.offset, words: best.words.join(" ") } : null;
}

function hideSecret() {
  revealed = false;
  if (current) renderText(current.text, []);
  $("secret").hidden = true;
  $("reveal").textContent = current ? "Reveal the secret" : "Check for a secret";
  stamp(false);
}

/** Light up the hidden letters and say the note in plain words, or say there's nothing. */
async function reveal() {
  if (revealed) {
    hideSecret();
    return;
  }
  const mine = ++request;
  try {
    const secret = await findSecret();
    if (mine !== request) return;
    revealed = true;
    $("secret").hidden = false;
    $("reveal").textContent = current ? "Hide the secret" : "Hide it again";
    if (!secret) {
      $("secret-label").textContent = "No secret here";
      $("secret-words").textContent = current
        ? "Just a lovely day at the seaside. Not every card hides something."
        : "Nothing hidden that we can see. Maybe it's just what it says.";
      $("secret-how").textContent = "";
      $("secret-words").classList.remove("is-found");
      status.textContent = "";
      stamp(false);
      return;
    }
    const where = await python.call<Look>("look", { text: text(), rule: secret.rule, offset: secret.offset, desk: onDesk() });
    if (mine !== request) return;
    if (current) renderText(current.text, where.positions);
    $("secret-label").textContent = current?.id === WRITTEN ? "Your secret note" : "The secret note";
    $("secret-words").textContent = `“${secret.words.toLowerCase()}”`;
    $("secret-words").classList.add("is-found");
    $("secret-how").textContent = `Hidden in the ${where.setting}.`;
    status.textContent = current?.id === WRITTEN ? "There's your note, hiding in plain sight." : "There it is!";
    stamp(Boolean(current));
  } catch (error) {
    console.error(error);
    status.textContent = "That didn't work. Try again.";
  }
}

/** What the desk says about the card before the secret is revealed. */
function invitation(): string {
  if (!current) return "Paste a letter, a poem or a song, then check it for a hidden note.";
  if (current.id === RECEIVED) return `${who(current)} hid a note on this card. Can you spot it? Reveal it when you give up.`;
  if (current.id === WRITTEN) return "Here's your card. Reveal the secret to see your note shine through.";
  return "Does this card hide a note? Read it closely, then reveal the secret.";
}

/** Put a card (or the blank one) on the desk, painted like its front, with its secret hidden. */
function show(id: string) {
  current = [...cards, ...extras].find((card) => card.id === id) ?? null;
  ++request; // forget any reveal still on its way for the last card
  const own = !current;
  cardOwn.hidden = !own;
  cardText.hidden = own;
  const card = $("card");
  card.dataset.scene = current?.scene ?? "own";
  const picture = $("card-picture");
  picture.dataset.scene = current?.scene ?? "own";
  picture.hidden = own;
  $("picture-place").textContent = current?.place ?? "";
  $("card-label").textContent = own
    ? "Your own words"
    : id === todayId
      ? "Today's postcard"
      : id === WRITTEN
        ? "Your postcard"
        : id === RECEIVED
          ? "A postcard for you"
          : `A card from ${current!.place}`;
  // Some senders write their own "Dear ..." and "love ...": don't say it twice.
  const message = current?.text.toLowerCase() ?? "";
  $("card-to").textContent = own
    ? "Paste a letter, a poem or a song you suspect:"
    : message.startsWith("dear ")
      ? ""
      : `Dear ${current!.to},`;
  $("card-from").textContent = own || message.includes("love ") ? "" : `Love from ${current!.sender} x`;
  $("postmark").textContent = own ? "YOUR TOWN" : current!.place.toUpperCase();
  renderRack();
  hideSecret();
  status.textContent = invitation();
}

/** A card for the desk that isn't on the rack (one you wrote, or one that came in a link). */
function deskCard(id: string, card: Received, secret: { offset: number; note: string } | null): Card {
  const { text, to, sender, place, scene } = card;
  const rule = secret ? "punctuation" : null; // a friend's card: no answer, so the reveal searches
  return { id, place, scene, to, sender, text, rule, offset: secret?.offset ?? 0, note: secret?.note ?? "" };
}

function putOnDesk(card: Card) {
  extras = [...extras.filter((c) => c.id !== card.id), card];
  show(card.id);
  $("card").focus({ preventScroll: true });
  $("card").scrollIntoView({ behavior: calm() ? "auto" : "smooth", block: "start" });
}

const noteInput = $<HTMLInputElement>("note");
const deskStatus = $("desk-status");
const position = () => Number(document.querySelector<HTMLInputElement>('input[name="position"]:checked')?.value ?? 3);
const story = () => document.querySelector<HTMLInputElement>('input[name="style"]:checked')?.value === "story";
const letterCount = () => noteInput.value.replace(/[^A-Za-z]/g, "").length;
let writing = false;

function renderCount() {
  const n = letterCount();
  const most = story() ? LONGEST_STORY : LONGEST_LIST;
  const each = story() ? "one sentence for each" : "one word of Nan's for each";
  $("note-count").textContent =
    n < SHORTEST ? `${n} letters: at least ${SHORTEST}, please` : n > most ? `${n} letters: ${most} at most` : `${n} letters: ${each}`;
  // The button stays pressable: a press on a missing or long note explains itself (see writeCard).
  $<HTMLButtonElement>("write").disabled = writing;
  $<HTMLButtonElement>("again").disabled = writing;
}

function renderStyle() {
  $("themes").hidden = !story();
  $("position-legend").textContent = story() ? "Hide it in each sentence's first word, at its…" : "Hide it in each word's…";
  renderCount();
}

const theme = () => document.querySelector<HTMLInputElement>('input[name="theme"]:checked')?.value ?? "beach";

/** The postcards to write on: little fronts like the rack's, one radio each. */
function renderThemes(themes: Theme[]) {
  const pick = Math.floor(Math.random() * themes.length); // a fresh visit starts on a surprise card
  $("theme-cards").replaceChildren(
    ...themes.map((t, i) => {
      const label = document.createElement("label");
      label.className = "theme-card";
      const input = document.createElement("input");
      input.type = "radio";
      input.name = "theme";
      input.value = t.id;
      input.checked = i === pick;
      const front = document.createElement("span");
      front.className = "front";
      front.dataset.scene = t.scene;
      const name = document.createElement("span");
      name.className = "front-greet";
      name.textContent = t.name;
      const place = document.createElement("span");
      place.className = "front-place";
      place.textContent = t.place;
      front.append(name, place);
      label.append(input, front);
      return label;
    }),
  );
}

/**
 * A change of card, letter or style. A written card is rewritten straight away; picking a
 * postcard also writes the note on it, or says what the note still needs.
 */
function choiceChanged(event: Event) {
  const picked = event.target as HTMLInputElement;
  const pickedCard = picked.name === "theme";
  const trouble = noteTrouble();
  if (!trouble && (current?.id === WRITTEN || pickedCard)) {
    void writeCard(current?.id === WRITTEN ? "same" : "fresh");
  } else if (pickedCard) {
    const name = picked.closest("label")?.querySelector(".front-greet")?.textContent ?? "That card";
    deskStatus.textContent = `${name} it is. ${letterCount() === 0 ? "Now type your secret note and press Write." : trouble}`;
  }
}

/** Why this note can't be written yet, in a sentence, or "" if it can. */
function noteTrouble(): string {
  const n = letterCount();
  const most = story() ? LONGEST_STORY : LONGEST_LIST;
  if (n === 0) return "Type your secret note in the box first.";
  if (n < SHORTEST) return `Your note needs at least ${SHORTEST} letters (it has ${n}).`;
  if (n > most) {
    const where = story() ? "A proper postcard" : "Nan's list";
    return `${where} fits ${most} letters at most (yours has ${n}).${story() ? " Nan's list takes up to 40." : ""}`;
  }
  return "";
}

/**
 * Write the card. "fresh" picks new words, "again" the next set, and "same" keeps the
 * words' seed so a change of theme, style or letter rewrites the card the visitor has.
 */
async function writeCard(mode: "fresh" | "again" | "same") {
  const trouble = noteTrouble();
  if (trouble) {
    deskStatus.textContent = trouble;
    noteInput.focus();
    return;
  }
  if (mode === "fresh") seed = Math.floor(Math.random() * 1_000_000);
  else if (mode === "again") seed += 1;
  writing = true;
  renderCount();
  try {
    const args = {
      note: noteInput.value,
      position: position(),
      seed,
      theme: theme(),
      to: $<HTMLInputElement>("to").value,
      sender: $<HTMLInputElement>("from").value,
    };
    const result = await python.call<Written>(story() ? "story" : "write", args);
    if (result.problem) {
      deskStatus.textContent = result.problem;
      return;
    }
    token = result.token;
    $("again").hidden = false;
    $("send").hidden = false;
    const where = story()
      ? `the ${ORDINAL[position()]} letter of each sentence's first word`
      : `the ${ORDINAL[position()]} letter of each of Nan's words`;
    deskStatus.textContent = `Done! Your note is in ${where}. Reveal the secret to check it, then send it.`;
    putOnDesk(deskCard(WRITTEN, result, { offset: position(), note: noteInput.value.trim().replace(/\s+/g, " ") }));
  } catch (error) {
    console.error(error);
    deskStatus.textContent = "The pen slipped. Try that again.";
  } finally {
    writing = false;
    renderCount();
  }
}

async function sendCard() {
  const link = `${location.origin}${location.pathname}#card=${token}`;
  try {
    await navigator.clipboard.writeText(link);
    deskStatus.textContent = "Link copied. Send it to a friend: the note stays hidden until they find it.";
  } catch {
    deskStatus.textContent = `Copy this link and send it: ${link}`;
  }
}

/** Open a postcard that arrived in a link (#card=...), if there is one. */
async function openFromLink() {
  const match = /^#card=([A-Za-z0-9_-]+)$/.exec(location.hash);
  if (!match) return false;
  const card = await python.call<Received>("unpack", { token: match[1] });
  if (card.problem) {
    show(todayId);
    status.textContent = card.problem;
    return true;
  }
  putOnDesk(deskCard(RECEIVED, card, null));
  return true;
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
  $<HTMLButtonElement>("reveal").disabled = false;
  $("reveal").addEventListener("click", () => void reveal());
  noteInput.addEventListener("input", renderCount);
  for (const choice of document.querySelectorAll('input[name="style"]')) choice.addEventListener("change", renderStyle);
  renderThemes(rack.themes);
  $("write-form").addEventListener("submit", (event) => {
    event.preventDefault();
    void writeCard("fresh");
  });
  $("again").addEventListener("click", () => void writeCard("again"));
  // Picking a card, a letter or a style writes the note on it straight away (or says what's missing).
  for (const choice of document.querySelectorAll('input[name="theme"], input[name="style"], input[name="position"]')) {
    choice.addEventListener("change", choiceChanged);
  }
  $("send").addEventListener("click", () => void sendCard());
  for (const field of ["note", "to", "from"]) $<HTMLInputElement>(field).disabled = false;
  renderStyle();
  window.addEventListener("hashchange", () => void openFromLink());
  cardOwn.addEventListener("input", () => {
    if (revealed) hideSecret(); // new words: the old answer no longer fits
  });
  if (!(await openFromLink())) show(todayId);
}

void start();
