# Who plays here: a research brief

Desk research for the Impractical Pythons gallery, done before redesigning the first three
projects. No interviews yet, so the personas below are *proto*-personas, built from where the
traffic comes from (the portfolio's "Projects" list) and from well-established web usability
findings. The test script at the end is how to check them with real people.

## Where visitors come from

The portfolio lists playful, one-idea apps (a camera whose photos develop when you shake the
phone, a PDF shrinker), each with a single plain sentence. Visitors arrive from that list
already expecting **one small, clever idea per page**, explained in one line.

## Proto-personas

| Who | Arrives because | Wants within a minute | Leaves when |
|---|---|---|---|
| **The skimmer** (a recruiter or hiring manager) | Clicked "Open" on the portfolio | To see that it works, looks considered, and is clearly someone's own idea | Nothing happens on screen; a loading wait has no explanation |
| **The tinkerer** (a developer or student) | Curious how Python runs in a browser | To play, then peek at the code and the idea behind it | The code is hidden, or the copy lectures before letting them play |
| **The friend** (someone sent the link) | "Try this, it's funny" | A laugh or a result worth sharing, ideally on a phone | It looks like homework, or text is tiny on mobile |

## What that means for every page

1. **Play first, explain later.** The toy is the hero and works with one tap or keystroke. The
   "how it works" goes underneath, short and friendly, with the Python one link away.
2. **Each page is its own attraction.** The gallery is a seaside pier; every project is a
   different stall on it with its own look, so the third page feels as fresh as the first.
3. **Something to show someone.** Each toy produces a result worth copying, sharing or
   screenshotting (a ticket, a secret message, a language fingerprint).
4. **Python loading is part of the show.** Pyodide takes a few seconds the first time; the
   wait says what is happening in the page's own voice and the controls show they're not ready.
5. **Phone-sized by default.** Big tap targets, no horizontal scrolling, readable at 375px.
6. **Fun copy, no jargon up top.** Module names (`defaultdict`, `re.sub`) live in the
   "Peek at the Python" part, not in the headline or the controls.
7. **Credit is visible and generous.** Every page and the gallery say plainly that the ideas
   were sparked by *Impractical Python Projects* by Lee Vaughan, with a link to the book, so
   visitors who enjoy it know where to go to level up.
8. **Accessible.** Keyboard reachable, visible focus, works in light and dark, respects
   reduced motion, and charts have a text equivalent.

## Checklist for each project page

- [ ] Someone who has never seen it knows what to do in five seconds.
- [ ] The first result appears without typing (a sample is preloaded).
- [ ] It looks unlike the other projects: its own palette, type and centrepiece.
- [ ] There is a result worth sharing or copying.
- [ ] Copy above the fold has no code words.
- [ ] Credit line with a link to the book is on the page.
- [ ] Works at 375px wide, in dark mode, by keyboard, and with reduced motion.

## A five-person hallway test (to run later)

Hand a phone to five people with the gallery open. Say only "Have a look around." Watch, don't
help. Afterwards ask:

1. What did you think this site was, at first glance?
2. Which one did you play with longest, and why?
3. Was there a moment you didn't know what to do?
4. Did you notice where the ideas came from?
5. Would you send any of these to a friend? Which one?

Five people reliably uncover most of the obvious problems; write down what they *did*, not just
what they said, and fold the findings back into this file.
