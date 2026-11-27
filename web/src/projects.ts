// The gallery's list of projects, in build order. Each one is a stall on the pier with its
// own look; `stall` picks that look on the home page (see .stall-* in styles.css).

export type Project = {
  number: number;
  slug: string;
  title: string;
  line: string;
  stall: "slots" | "talk" | "rock";
  cue: string;
};

export const projects: Project[] = [
  {
    number: 1,
    slug: "alias-slots",
    title: "Alias Slots",
    line: "A fruit machine that pays out ridiculous secret identities. Hold the reels you love and spin the rest.",
    stall: "slots",
    cue: "Pull the lever",
  },
  {
    number: 2,
    slug: "code-talk",
    title: "Code-Talk",
    line: "Pig Latin with a secret handshake. Scramble a message for a friend, then turn it back.",
    stall: "talk",
    cue: "Open the case file",
  },
  {
    number: 3,
    slug: "letter-bars",
    title: "Letter Bars",
    line: "Seaside rock pulled from your words: a candy stick for every letter. Every language has its own flavour.",
    stall: "rock",
    cue: "Weigh your words",
  },
];
