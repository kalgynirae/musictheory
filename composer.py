import collections
import random

random.seed(5)

def basic_chord_progression(key, phrases=2):
    transitions = {
        0: [1, 5],
        1: [3, 6, (2, 4), (5, 7)],
        2: [4, (5, 7), 1],
        3: [6, (2, 4), (5, 7), 1],
        4: [2, (5, 7), 1],
        5: [7, 6, 1],
        6: [(2, 4), (5, 7), 1],
        7: [5, 1],
    }
    #minor_chords = [7, 3, 6, [2, 4], 5, 1]
    progression = []
    for n in range(phrases):
        phrase = [choose(transitions[0])]
        while True:
            new_chord = choose(transitions[phrase[-1]])
            phrase.append(new_chord)
            if len(phrase) > random.randrange(3,10):
                if n % 2 == 0:
                    # Half cadence
                    if new_chord in [6, 2, 4, 1]:
                        phrase.append(5)
                        break
                else:
                    # Authentic cadence
                    if new_chord in [2, 4, 6, 1, 7]:
                        phrase.append(5)
                        phrase.append(1)
                        break
        progression.append(phrase)
    return progression

def choose(choices):
    while True:
        try:
            choices = random.choice(choices)
        except TypeError:
            break
    return choices
