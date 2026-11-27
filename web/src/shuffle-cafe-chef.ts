// Chef's choice: Python invents whole-phrase anagrams of the name on the board, and the page
// serves them like a tasting flight. Five at a time on an order ticket, each one kept or sent
// back, with the kept ones collected on an order card worth copying. The full list (up to 500)
// is one tap away, but it's never the first thing you see.
import type { Python } from "./py/python";

type ChefResult = { phrases: string[]; hidden: number };

const FLIGHT = 5;

const $ = <T extends HTMLElement>(id: string) => document.getElementById(id) as T;
const nameInput = $<HTMLInputElement>("phrase-name");
const nameLabel = $("chef-name");
const table = $("chef-table");
const ticket = $<HTMLOListElement>("ticket");
const status = $("chef-status");
const ask = $<HTMLButtonElement>("chef-ask");
const next = $<HTMLButtonElement>("chef-next");
const menu = $<HTMLDetailsElement>("chef-menu");
const menuTitle = $("chef-menu-title");
const menuList = $<HTMLUListElement>("chef-menu-list");
const orderCard = $("order-card");
const orderList = $<HTMLUListElement>("order-list");
const orderCopy = $<HTMLButtonElement>("order-copy");

let python: Python;
let name = "";
let phrases: string[] = [];
let served = 0; // how many phrases have been brought out so far
let kept: string[] = [];
let request = 0;
const calm = () => matchMedia("(prefers-reduced-motion: reduce)").matches;

function loadOnBoard(phrase: string) {
  document.dispatchEvent(new CustomEvent("cafe:load", { detail: phrase }));
}

function button(text: string, className: string, onClick: () => void) {
  const b = document.createElement("button");
  b.type = "button";
  b.className = className;
  b.textContent = text;
  b.addEventListener("click", onClick);
  return b;
}

function renderOrder() {
  orderCard.hidden = kept.length === 0;
  orderList.replaceChildren(
    ...kept.map((phrase) => {
      const li = document.createElement("li");
      li.textContent = phrase;
      return li;
    }),
  );
}

function toggleKeep(phrase: string, keepButton: HTMLButtonElement) {
  const keeping = !kept.includes(phrase);
  kept = keeping ? [...kept, phrase] : kept.filter((p) => p !== phrase);
  keepButton.setAttribute("aria-pressed", String(keeping));
  keepButton.textContent = keeping ? "Kept" : "Keep";
  renderOrder();
}

function sendBack(li: HTMLLIElement) {
  if (calm()) {
    li.remove();
  } else {
    li.classList.add("is-sent-back");
    li.addEventListener("animationend", () => li.remove(), { once: true });
  }
  if (ticket.children.length <= 1 && served < phrases.length) status.textContent = "Ticket's empty. Ask for five more?";
}

function ticketLine(phrase: string) {
  const li = document.createElement("li");
  const dish = button(phrase, "dish", () => loadOnBoard(phrase));
  dish.title = "Put it on the board";
  const keep = button(kept.includes(phrase) ? "Kept" : "Keep", "stamp stamp-keep", () => toggleKeep(phrase, keep));
  keep.setAttribute("aria-pressed", String(kept.includes(phrase)));
  keep.setAttribute("aria-label", `Keep ${phrase}`);
  const back = button("Send back", "stamp stamp-back", () => sendBack(li));
  back.setAttribute("aria-label", `Send back ${phrase}`);
  const stamps = document.createElement("span");
  stamps.className = "stamps";
  stamps.append(keep, back);
  li.append(dish, stamps);
  return li;
}

function serveFlight() {
  const flight = phrases.slice(served, served + FLIGHT);
  served += flight.length;
  ticket.replaceChildren(...flight.map(ticketLine));
  next.hidden = served >= phrases.length;
  status.textContent =
    served >= phrases.length
      ? `That's the whole menu: ${phrases.length} ${phrases.length === 1 ? "phrase" : "phrases"}. Tap one to put it on the board.`
      : `Serving ${served} of ${phrases.length}. Tap a phrase to put it on the board and tweak it.`;
}

function renderMenu() {
  menu.hidden = phrases.length <= FLIGHT;
  menuTitle.textContent = `See the full menu (${phrases.length} phrases)`;
  menuList.replaceChildren(); // filled when opened: 500 buttons nobody asked for yet can wait
  menu.open = false;
}

menu.addEventListener("toggle", () => {
  if (!menu.open || menuList.children.length) return;
  menuList.replaceChildren(
    ...phrases.map((phrase) => {
      const li = document.createElement("li");
      li.append(button(phrase, "menu-dish", () => loadOnBoard(phrase)));
      return li;
    }),
  );
});

async function cook() {
  const mine = ++request;
  const cooking = name;
  ask.disabled = true;
  next.hidden = true;
  ticket.replaceChildren();
  status.textContent = `The chef is trying combinations of ${cooking}…`;
  try {
    const result = await python.call<ChefResult>("chef", { name: cooking });
    if (mine !== request) return;
    phrases = result.phrases;
    served = 0;
    renderMenu();
    if (phrases.length) {
      serveFlight();
    } else {
      status.textContent = `The chef couldn't use every letter of ${cooking}. Try adding or dropping a letter, or build a phrase yourself above.`;
    }
  } catch (error) {
    console.error(error);
    status.textContent = "The kitchen's in a muddle. Ask the chef again.";
  }
  ask.disabled = false;
}

function setName(value: string) {
  name = value.trim();
  request++; // forget any order still cooking for the old name
  nameLabel.textContent = name || "your name";
  table.textContent = name ? `Table: ${name}` : "Table for one";
  phrases = [];
  served = 0;
  kept = [];
  renderOrder();
  renderMenu();
  ticket.replaceChildren();
  next.hidden = true;
  const letters = name.replace(/[^a-z]/gi, "");
  ask.disabled = !letters;
  status.textContent = letters ? `Ask the chef to cook up phrases from ${name}.` : "Type a name above for the chef to work with.";
}

export async function startChef(py: Python) {
  python = py;
  ask.addEventListener("click", () => void cook());
  next.addEventListener("click", serveFlight);
  orderCopy.addEventListener("click", async () => {
    const text = `${name} =\n${kept.join("\n")}`;
    try {
      await navigator.clipboard.writeText(text);
      status.textContent = `Order copied. Send it to someone called ${name}!`;
    } catch {
      status.textContent = `Copy this: ${kept.join(", ")}`;
    }
  });
  document.addEventListener("cafe:name", (event) => setName((event as CustomEvent<string>).detail));
  setName(nameInput.value);
  await cook(); // the first flight arrives without asking, so there's something to see
}
