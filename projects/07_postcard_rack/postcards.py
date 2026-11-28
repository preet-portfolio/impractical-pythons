"""The postcards on the rack, all written for this stall.

Most hide a note: a few letters, picked out by one of the rules in
``null_finder``, spell something the sender didn't want the postman to
read. One card is just a postcard, so the rack keeps you honest: not
every letter has a secret.

Writing a card like this by hand is fiddly (an extra comma or an
apostrophe restarts the count), so a test checks every one.
"""

from datetime import date

OPENING_DAY = date(2026, 11, 1)  # the rack went up the same day as the telegraph

POSTCARDS = [
    {
        "id": "pier",
        "place": "Redcliff Pier",
        "scene": "pier",
        "to": "Mo",
        "sender": "Jo",
        "text": (
            "Dear Mo, Cracking weather here! Hot sun all day. Ice creams twice "
            "before lunch. Pier is packed with folk. Sandcastles as far as you "
            "can see. All the gulls are cheeky. Tide comes in very fast. Nan "
            "fell asleep in a deckchair. Only one cloud in the sky. Our hotel is "
            "lovely. Now off for tea with the gang"
        ),
        "rule": "punctuation",
        "offset": 1,
        "note": "chips at noon",
    },
    {
        "id": "beach-huts",
        "place": "Gullsand Bay",
        "scene": "huts",
        "to": "Sam",
        "sender": "the Pikes",
        "text": (
            "Hi Sam! Skies are blue and the sea is warm. We swam twice. Lying on "
            "the beach all day. Mum lost her sunhat. Snacks are pricey. Odd "
            "little town. Wet dog in the cafe. Free deckchairs! Ugly gulls "
            "everywhere. Unpacked at last. Rock pools are fun. Smashing time. "
            "See you soon"
        ),
        "rule": "punctuation",
        "offset": 2,
        "note": "key under gnome",
    },
    {
        "id": "lighthouse",
        "place": "Hollow Point Lighthouse",
        "scene": "lighthouse",
        "to": "Aunt Win",
        "sender": "Rosie",
        "text": (
            "Greetings from the bay. Wish you were here. Sheep on the cliffs. "
            "Beach is busy. Huge waves. Shutters rattle all night. Hello from "
            "Nan. Fully booked hotel. Mist rolled in. Lots of sunshine too. "
            "Shops close at five. Sally says hi. Theatre was fun. Hammocks on "
            "the lawn. Dry by teatime. Ashore by noon. Heaps of shells. Into "
            "town later"
        ),
        "rule": "punctuation",
        "offset": 3,
        "note": "seagull stole my hat",
    },
    {
        "id": "donkeys",
        "place": "Donkey Sands",
        "scene": "donkeys",
        "to": "Grandma",
        "sender": "Ted",
        "text": (
            "Brilliant trip so far. Rain held off and Isla met Nell at the "
            "beach. Grandad came too. Aunt Sue brought sandwiches. Pa dozed off. "
            "After lunch Dad rode a donkey. Everyone cheered"
        ),
        "rule": "capitals",
        "offset": 1,
        "note": "bring a spade",
    },
    {
        "id": "rock-pools",
        "place": "Winkle Cove",
        "scene": "rocks",
        "to": "Kit",
        "sender": "Lou",
        "text": "Big umbrellas cover kids eating toast slowly",
        "rule": "words",
        "offset": 1,
        "note": "buckets",
    },
    {
        "id": "arcade",
        "place": "Silver Sands Arcade",
        "scene": "arcade",
        "to": "Ali",
        "sender": "Bex",
        "text": (
            "Dear Ali, Postcards are dear here! It rained once. Everyone else is "
            "sunburnt. Rock pools full of crabs. Amazing chips. Tide was out all "
            "morning. Seals spotted off the point. Ice cream for breakfast. "
            "Xylophone band on the pier tonight"
        ),
        "rule": "punctuation",
        "offset": 1,
        "note": "pier at six",
    },
    {
        "id": "caravan",
        "place": "Seaview Caravan Park",
        "scene": "caravan",
        "to": "Jas",
        "sender": "Mei",
        "text": (
            "We agreed to share a cosy caravan: Ash, Bo, Stella and Otto. We "
            "tried the maze and liked the snacks most"
        ),
        "rule": "nth",
        "offset": 2,
        "note": "ghost train",
    },
    {
        "id": "promenade",
        "place": "The Promenade",
        "scene": "prom",
        "to": "Pat",
        "sender": "Bea",
        "text": (
            "Dear Pat, the weather has been glorious all week. We walked along "
            "the prom every morning and had fish and chips on the harbour wall. "
            "Tom says hello. See you on Sunday, love Bea"
        ),
        "rule": None,  # just a postcard
        "offset": 0,
        "note": "",
    },
]


def with_notes() -> list[dict]:
    """The postcards that really do hide something."""
    return [card for card in POSTCARDS if card["note"]]


def postcard_number(day: date) -> int:
    """Count the days since the rack went up: card No. 1 on opening day."""
    return max(1, (day - OPENING_DAY).days + 1)


def todays_postcard(day: date) -> dict:
    """The postcard at the front of the rack today (always one with a note).

    The date picks it, so everyone who visits on the same day gets the
    same card, with no server to hand it out.
    """
    cards = with_notes()
    return cards[(postcard_number(day) - 1) % len(cards)]
