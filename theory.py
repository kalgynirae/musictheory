"""
Basic music theory stuff.

It's easy to create pitches
>>> Pitch('a4')
Pitch('a4')
>>> Pitch('as2')
Pitch('as2')
>>> Pitch('fis6')
Pitch('fis6')

We prefer Dutch note names to using "b" to mean "flat"
>>> Pitch('ab4')
Pitch('as4')

You can augment pitches like so;
>>> Pitch('a3').augment(Interval('m3'))
Pitch('c4')
>>> Pitch('a3').augment(Interval('A3'))
Pitch('cisis4')
>>> Pitch('a3').augment(Interval('4'))
Pitch('des4')

"""
from math import log

class Pitch:
    """Represents a specific frequency and MIDI pitch number

    """
    @property
    def frequency(self):
        return 440.0 * (2 ** ((self._midi_pitch - 69) / 12))

    def Pitch(self, name):
        match = re.match(r"([ABCDEFG])([0-9])")
        if match:
            pass
        else:
            raise ValueError()

class Interval:
    """Represents the distance between two notes

    """
    def Interval(self, name):
        match = re.match(r"([AMmd])([1-9][0-9].)", name)
        if match:
            self._quality = match.group(1)
            self._generic = match.group(2)
        else:
            raise ValueError()
