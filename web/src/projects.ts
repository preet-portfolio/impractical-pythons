// The gallery's list of projects, in build order.

export type Project = {
  number: number;
  slug: string;
  title: string;
  line: string;
  python: string;
};

export const projects: Project[] = [
  {
    number: 1,
    slug: "alias-slots",
    title: "Alias Slots",
    line: "A fruit machine for ridiculous aliases. Hold the reels you like and spin the rest.",
    python: "tuples, random.Random(seed), dataclasses, a base-36 share code",
  },
];
