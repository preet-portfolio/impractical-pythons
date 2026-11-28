"""How often each letter turns up in ordinary English text.

Two stalls need this table: Letter Bars draws it next to your own text,
and Pier Telegraph uses it to tell a shuffled message (same letters,
new order) from a swapped one (every letter replaced by another).
"""

# Typical share of each letter in English text, in percent. These are the
# widely quoted figures from Robert Lewand's "Cryptological Mathematics"
# (2000), the same table Wikipedia's "Letter frequency" article uses.
ENGLISH = {
    "a": 8.2, "b": 1.5, "c": 2.8, "d": 4.3, "e": 12.7, "f": 2.2,
    "g": 2.0, "h": 6.1, "i": 7.0, "j": 0.15, "k": 0.77, "l": 4.0,
    "m": 2.4, "n": 6.7, "o": 7.5, "p": 1.9, "q": 0.095, "r": 6.0,
    "s": 6.3, "t": 9.1, "u": 2.8, "v": 0.98, "w": 2.4, "x": 0.15,
    "y": 2.0, "z": 0.074,
}  # fmt: skip
