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

## Anagram tools: what's out there (Shuffle Café, part 4)

Before building the automatic anagram generator and the letter sieve, we looked at the tools the
book points to: the Internet Anagram Server (its main and advanced pages, and its Hall of Fame),
dCode's anagram generator, and Jumble. (Wordplays refused our visit.)

**What they do**

- **Form first.** dCode offers a dictionary in eight languages and three sizes, must-include
  and must-exclude boxes, word-count modes and minimum lengths, and some labels only make sense
  after reading its FAQ. The Anagram Server's advanced page has eleven settings.
- **Volume, not choice.** You pick 500, 1,000, 5,000, 10,000 or "All" and get a flat list.
  Finding the one good anagram in it is left to you.
- **Clutter.** A second tool, a famous-anagrams list, shop links and donation prompts share
  the page.
- **Dead ends.** "No result" appears when a filter is too strict, and the way out is in the
  help text.
- **What people celebrate.** The Hall of Fame's favourites use every letter, are funny or
  surprising, and above all *mean something about the original*. Software can't judge that;
  people can.
- **Jumble** is a puzzle with a payoff: unscramble, then get the punchline.

**What our visitors need instead**

| Who | The usual tool gives them | We give them |
|---|---|---|
| The skimmer | A form and a wall of text | A result before they type, and one clever moment within seconds |
| The tinkerer | A black box | The working on show: how many guesses each filter threw out, and *why* |
| The friend | Homework | Their own name turned into something funny, on a card worth sending |

**Rules for these features**

1. **Curate, don't dump.** Rank the results, serve a few at a time, let people keep favourites;
   the long list is one tap away, not the default.
2. **Show the working.** Numbers dropping through each filter are the spectacle.
3. **Explain every rejection in plain words** ("hardly any English word starts with *vl*").
4. **One or two controls at most.** Good defaults instead of settings.
5. **End on something shareable.**
6. **Never a bare "no result".** Always suggest the next thing to try.

## Telegrams people send: research for the Pier Telegraph

Desk research done after the first version of the stall, looking at online cipher tools,
escape-room and daily puzzle games, code-breaking museum exhibits and kids' spy kits, and
walking each proto-persona through the page. Summarised here in our own words.

**What the research found**

- **Sending a telegram was a chore.** The receiver needed the scrambled words *and* the key,
  sent separately. Almost nobody shares a joke in two messages.
- **Cracking was too easy.** Reading the waiting telegram straight down every column already
  got 11 of its 15 words right, and a live "N right" count after every tap turned the puzzle
  into hot-and-cold clicking.
- **Nothing brought people back.** Daily puzzles with a spoiler-free result to paste into a
  group chat are what make the popular word games spread.
- **The wait for Python needs a voice.** A few silent seconds on a phone look broken.
- **Cipher sites feel like workbenches.** The stall's physical rack, tape and stamp are its
  advantage over them; keep the maths below the fold.

**What we changed**

| Finding | Change |
|---|---|
| Two messages to share one telegram | **Challenge link**: one URL with the scrambled words and a one-way fingerprint of the answer, never the key or the message |
| No way to answer back | **Send a reply** button under the DELIVERED stamp |
| Cracking was over in seconds | A new route for every telegram, rolled until reading straight down gets at most a fifth of the words |
| Live score made it guesswork | **Check the route** button; the score only shows when you check, and the count of checks is kept |
| No reason to return | **A telegram a day**, the same for everyone, picked by the date with no server |
| Nothing to show friends | **Copy my result**: "cracked in 3 checks", with no spoilers |
| Typing on a phone is a chore | **Another message** fills the form with a ready-made seaside telegram |
| Silent loading | The clerk's own words while Python loads ("Stringing the telegraph wire…") |
| Code hidden behind a repo | "Peek at the Python" opens the route cipher file itself |
| Cramped racks on phones | Phones get racks of up to 5 columns, and long words shrink to fit their pigeonhole |

**Left for later:** letting senders add a couple of their own code words, a muted-by-default
sound for the stamp, and showing the Python inside the page.


## The night clerk and the rail fence (Pier Telegraph, part 3)

Notes from building the rest of chapter 4 into the stall, walked through with the
proto-personas.

- **A brute force that "just answers" would have been a lie.** Plain rules ranked the right
  route anywhere from 1st to 1,400th, because the clerk can't tell one ordinary word from
  another. Instead of hiding that, the page makes it the game: you give the clerk hunches
  (word pairs you're sure of), it does the counting. Three hunches put the answer in its top
  five for every daily telegram, and a test keeps it that way.
- **Hunches are taps, not typing.** The telegram's words are chips: tap one, then the word you
  think follows it. On a phone that's two taps per hunch, with no spelling to get wrong.
- **The clerk's answer goes back on the rack.** "Try this route" loads a reading into the
  Crack counter, and the visitor still presses Check, so the DELIVERED stamp is still theirs.
- **Big numbers need a picture.** The key-count chart shows ticket rolls on a log scale with
  the real numbers beside them, and it's a real table for screen readers.
- **Four counters on one page need signposts.** Brass tabs under the sign jump to each one and
  stay in reach; on a phone they shrink to one row.
- **The dictionary is heavy.** It loads only when the rail fence first needs words, with a
  line in the office's voice while it does.


## The Postcard Rack (chapter 5, the Trevanion cipher)

Notes from building the null-cipher finder as its own stall, checked against the
proto-personas and the checklist.

- **The note shows itself in place.** The book prints a line of letters per offset. Here the
  letters the glass lands on light up inside the handwriting, so the skimmer sees the trick
  work in one tap without reading a word of explanation.
- **Today's card is on the desk at load, but not solved.** The glass starts on the plain
  punctuation rule; turning it is the game. A rack of seven more cards (one a decoy with
  nothing to find) means there's always another to try.
- **A lucky reading isn't a win.** Short strings of "a", "at" and "me" read as 100% words. The
  tag says so in plain words ("real words, but tiny ones. That's what luck looks like") and the
  stamp only lands on a real note.
- **"Try every setting" is the jailer's view.** It ranks every rule and count, and one tap sets
  the glass to any of them, so the tinkerer can see why the winner wins.
- **Your own words.** A blank card takes any pasted text; the friend can test a song lyric.
- **Phones:** words never break around a magnified letter, the stamp has its own strip at the
  foot of the card, and the rack goes two across.

**Not met yet:** there's no result to copy or send. Writing your own hidden-note postcard (the
book's next project, set aside for now) is the natural shareable result.

**Part 2, the writing desk:** now met. The friend persona gets a link that opens on "A
postcard for you" with the sender's name, and has to find the note with the glass; the
sender tests their card on the desk before sending. Choices made for the personas:

- **Typing is short.** One note field with a live letter count, three big position chips,
  and optional To/From names. A phone keyboard never covers the button that matters.
- **No dead ends.** Too short, too long or unkind notes get one plain sentence on the desk;
  a smudged link falls back to today's card and says what happened.
- **The answer never travels.** The link holds only the card, so the fun survives a forward.
- **Kind words only.** Nan's words pass a stricter filter than the rest of the pier, because
  they appear on a card the visitor didn't write word by word.

**Part 3, proper postcards:** five themes (beach, pier, rain, caravan, fish and chips) turn a
note into a postcard that reads like a real day out, written by Python in the browser.

- **One more choice, not five more fields.** "A proper postcard" reveals a row of five theme
  chips, one already picked at random, so the visitor can still just type and press Write.
- **The postmark and picture travel with it**, so the friend sees "Harbour Wall", not Nan's
  club.
- **Honest about short notes.** Testing as a visitor showed the glass calling "go to the
  pub" luck. On desk cards the writer's settings now accept short words, the sender's own
  note always counts, and a friend with mostly real words is told to read it themselves.
- **Checked at 375px in dark mode and by keyboard** (arrow keys move between themes, with a
  visible focus ring). No new motion.

