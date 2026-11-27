# DELIBERATELY MESSY: this file breaks PEP 8 and PEP 257 on purpose so Pylint
# has something to complain about. See STYLE_CLINIC.md. tidy_slots.py is the fixed twin.
import sys, random
import os
spinCount = 0
FirstWords = ("Waffle", "Socket", "Pebble", "Turnip", "Velcro", "Marzipan", "Gadget")
LastWords = ("McNoodle", "Featherstone", "Bumbercrumb", "Snorkelton", "Puddleby")
TAGS = ("the Unbreakable Teaspoon", "who Knows a Guy", "of the Overdue Library Book")
def SpinOnce():
    global spinCount
    spinCount = spinCount + 1
    a = random.choice(FirstWords); b = random.choice(LastWords)
    c = random.choice(TAGS)
    return "%s %s %s" % (a, b, c)
print("\nWelcome to the (messy) Snack Agent alias spinner!   ")
print("Press Enter to spin, or type n and Enter to stop. Every alias gets printed in red, mostly.")
while True:
    name = SpinOnce()
    print("\n\n" + name + "\n", file=sys.stderr)
    try:
        answer = input("Spin again? ")
    except:
        break
    if (answer.lower() == "n") == True:
        break
print("You spun %d times. Press Enter to leave." % spinCount)
try:
    input()
except:
    pass
