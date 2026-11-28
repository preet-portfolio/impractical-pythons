"""Eight ready-made seaside postcards for hiding a note in, one sentence per letter.

Every sentence on these cards is "Somebody did something.": a one-word
subject, then an ending from the theme. The subject carries the note's
letter (its 2nd, 3rd or 4th letter), and the full stop after each
sentence restarts the reading glass's count for the next one.

Two rules keep that working, and the tests check both:

* nothing here contains a punctuation mark, except the single mark at
  the very end of each opening line (that mark starts the count);
* every ending is past tense and names nobody, so it fits any subject:
  "Ezra lost a flip flop", "Grandad lost a flip flop", "Cousins lost a
  flip flop".

All the names and lines were written for this stall.
"""

# Who did it: first names from all over, plus family. Plenty of names
# means every letter has someone to carry it, even q, x, z and j.
SUBJECTS = """
    Abe Ada Adam Aditi Ahmed Aisha Ajay Alba Alexa Alfie Ali Amara Amir Amy
    Ana Anja Anya Arlo Arun Asha Ava Axel Aziz Bea Ben Benji Bilal Bo Bryn
    Cal Cara Chen Chloe Cleo Coco Dara Dev Dexter Dina Ebo Eden Edie Eli
    Ella Elsa Emeka Esme Evie Ezra Faye Femi Finn Flo Freya Gemma Gita Gus
    Hana Hugo Ibby Ida Iggy Ike Imran Iqbal Isla Ivan Ivy Jacqui Jade Jaz
    Jen Jiya Jo Joel Joss Jude Juno Kai Kaz Kemi Kiki Kit Kofi Lars Lena
    Leo Lex Lily Liza Lizzie Lola Luca Lulu Mae Maja Max Maya Mei Milo Mo
    Nadia Nell Nia Nico Nina Noor Nye Obi Olaf Oli Omar Oona Ozzy Pablo
    Pip Priya Quinn Raj Raja Raquel Rex Ria Rhys Rory Roxy Ruby Rumi Sade
    Sam Sana Seb Shay Sita Suki Suzy Taj Tara Teo Theo Tilly Tomas Uma Una
    Usha Uzma Val Vera Vic Vijay Viv Wes Wilf Willa Xander Yan Yara Yuki
    Yusuf Zac Zara Zeb Zoe Zuri
    Ace Agnes Akira Ayla Clive Edwin Effie Erika Etta Ewan Freddie Gabby
    Gwen Hope Ichiro Ifan Kyle Leah Marco Noah Olive Opal Otto Owen Peggy
    Pippa Poppy Reggie Robbie Rocco Rowan Sanjay Selwyn Shawn Sophie Stan
    Mum Dad Nan Nana Gran Grandad Grandma Auntie Uncle Cousins Everyone
""".split()  # noqa: SIM905

THEMES = [
    {
        "id": "beach",
        "name": "Beach day",
        "place": "Gullsand Bay",
        "scene": "huts",
        "opening": "Wish you were here!",
        "endings": [
            "built a sandcastle with a moat",
            "found a crab under a rock",
            "paddled in the freezing sea",
            "dug a hole all the way to the water",
            "fell asleep in a deckchair",
            "lost a flip flop to the tide",
            "found a shell shaped like a heart",
            "flew a kite over the dunes",
            "spotted a seal near the rocks",
            "got sand in every sandwich",
            "won the race to the beach huts",
            "jumped over seven waves in a row",
            "made a mermaid out of sand",
            "collected a bucket of pebbles",
            "chased the tide out and back again",
            "wrote hello in giant letters on the sand",
            "shared a flask of hot tea",
            "waved at the boats going past",
            "napped under a stripy umbrella",
            "skimmed a stone five times",
        ],
    },
    {
        "id": "pier",
        "name": "On the pier",
        "place": "Bramble Bay Pier",
        "scene": "pier",
        "opening": "Greetings from the pier!",
        "endings": [
            "won a teddy on the claw machine",
            "spent all the coppers in the arcade",
            "rode the carousel three times",
            "screamed all the way round the ghost train",
            "ate candy floss as big as a cloud",
            "watched the anglers at the very end",
            "got a fortune from the brass machine",
            "danced to the man with the accordion",
            "bought a stick of rock with our names in it",
            "beat everyone at air hockey",
            "had a go on the dodgems",
            "spotted dolphins from the railings",
            "lost a sun hat in the wind",
            "posed for a photo by the big wheel",
            "counted the planks all the way to the end",
            "listened to the waves under the boards",
            "shared a bag of hot doughnuts",
            "won a prize on the penny falls",
            "rang the bell on the strongman game",
            "fed a very bold seagull a chip",
        ],
    },
    {
        "id": "rain",
        "name": "Rainy day",
        "place": "Saltmarsh Prom",
        "scene": "prom",
        "opening": "Rain again but we are having fun!",
        "endings": [
            "played cards in the cafe",
            "read comics in the bus shelter",
            "jumped in every puddle on the prom",
            "steamed up the windows of the chip shop",
            "found a museum full of old diving suits",
            "made a fort from the beach towels",
            "watched the storm roll in over the sea",
            "drank hot chocolate with cream on top",
            "won every game of snap",
            "wore a bin bag as a raincoat",
            "spotted a rainbow over the harbour",
            "sang in the bandstand to keep dry",
            "dried wet socks on the radiator",
            "finished a jigsaw of a sunny beach",
            "ran for the tram and just missed it",
            "bought an umbrella covered in ducks",
            "played crazy golf in the drizzle",
            "raced raindrops down the window",
            "laughed at the soggy seagulls",
            "had soup in the old tea room",
        ],
    },
    {
        "id": "caravan",
        "name": "Caravan holiday",
        "place": "Clifftop Caravan Park",
        "scene": "caravan",
        "opening": "Greetings from the caravan!",
        "endings": [
            "cooked sausages on the little stove",
            "slept on the bunk that folds down",
            "won the talent show in the clubhouse",
            "found the swimming pool freezing",
            "played rounders on the big field",
            "made friends with the family next door",
            "toasted marshmallows after dark",
            "heard owls hooting all night",
            "came second in the clubhouse quiz",
            "hired a bike for the coast path",
            "squeezed nine people round the table",
            "spotted a fox by the bins",
            "watched the sunset from the steps",
            "learned to play swingball",
            "fetched fresh rolls every morning",
            "got lost on the way to the shower block",
            "taught everyone a new card game",
            "sang along at the disco",
            "ate breakfast on the grass",
            "found a frog under the step",
        ],
    },
    {
        "id": "chips",
        "name": "Fish and chips",
        "place": "Harbour Wall",
        "scene": "rocks",
        "opening": "Fish and chips by the harbour!",
        "endings": [
            "ordered a huge cod and chips",
            "dropped a chip and a gull got it",
            "asked for extra salt and vinegar",
            "tried mushy peas for the first time",
            "shared a battered sausage",
            "sat on the harbour wall to eat",
            "licked the vinegar off the paper",
            "bit a pickled onion and pulled a face",
            "counted the boats coming in",
            "saved one chip for later",
            "got ketchup on everything",
            "watched the fishing boats unload",
            "had a pineapple fritter for pudding",
            "kept the chips warm under a coat",
            "blew on every chip to cool it",
            "built a tower of little wooden forks",
            "went back for a second portion",
            "fed the last crust to the ducks",
            "picked out all the crispy bits",
            "ate the lot in five minutes flat",
        ],
    },
    {
        "id": "lighthouse",
        "name": "Lighthouse walk",
        "place": "Beacon Point",
        "scene": "lighthouse",
        "opening": "Greetings from the lighthouse!",
        "endings": [
            "climbed all the steps to the top",
            "counted every step on the way down",
            "waved at the keeper from the rocks",
            "watched the beam sweep across the sea",
            "spotted a ship right on the horizon",
            "found a crab in a rock pool",
            "saw the sun go down behind the light",
            "heard the foghorn and jumped a mile",
            "bought a tiny lighthouse for the shelf",
            "had a picnic on the cliff top",
            "looked through the big brass telescope",
            "spotted puffins on the cliffs",
            "painted the lighthouse in red and white",
            "learned how the great lamp turns",
            "held on to a hat in the gale",
            "found a message in a bottle",
            "watched the waves crash on the rocks",
            "saw a seal sunbathing below",
            "walked the cliff path all the way round",
            "fell asleep to the sound of the sea",
        ],
    },
    {
        "id": "donkeys",
        "name": "Donkey rides",
        "place": "Sunny Sands",
        "scene": "donkeys",
        "opening": "Donkey rides on the beach today!",
        "endings": [
            "rode a donkey in a straw hat",
            "fed a carrot to the smallest donkey",
            "brushed a donkey until it shone",
            "got a rosette for the best rider",
            "patted every donkey in the line",
            "won the donkey derby by a nose",
            "built a sandcastle stable",
            "picked the donkey with the floppy ears",
            "gave the donkeys a bucket of water",
            "ate an ice cream on the sea wall",
            "took a photo with a sleepy donkey",
            "learned all the donkey names",
            "laughed when a donkey sneezed",
            "bought a toy donkey from the stall",
            "rode along the sand to the pier and back",
            "waited ages in the queue and loved it",
            "held the reins with no help at all",
            "named a sandcastle after a donkey",
            "wore a cowboy hat for the ride",
            "shared an apple with a donkey",
        ],
    },
    {
        "id": "arcade",
        "name": "Arcade night",
        "place": "Golden Mile Arcades",
        "scene": "arcade",
        "opening": "Greetings from the arcades!",
        "endings": [
            "won a mountain of tickets",
            "swapped the tickets for a rubber duck",
            "beat the high score on the racing game",
            "lost every coin in the coin pusher",
            "danced on the flashing dance machine",
            "hooked a plastic duck",
            "grabbed a teddy with the claw at last",
            "shot ten hoops in a row",
            "drove the bumper cars into everyone",
            "had the best go on the pinball",
            "found a coin on the carpet",
            "won a glow stick bracelet",
            "played the drums on the rhythm game",
            "rolled a ball into the top hole",
            "tried the fortune teller machine",
            "spent the whole morning on skee ball",
            "counted the prize tickets twice",
            "bought a bag of pick and mix",
            "ate popcorn on the way out",
            "won a plastic crown",
        ],
    },
]

THEMES_BY_ID = {theme["id"]: theme for theme in THEMES}
