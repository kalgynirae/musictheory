"""Basic music theory stuff.

>>> a = Pitch('a4')
>>> b = Pitch('cis4')
>>> b - a
Interval('M3')
>>> a.augment(Interval('A3'))
Pitch('cisis4')

"""
import re
from math import log

class Pitch:
    """Represents a specific frequency and MIDI pitch number

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
    name_regex = re.compile(r"(?P<class>as|es|[a-g])" +
                            r"(?P<accidentals>(?:es|is)*|[b#]*)" +
                            r"(?P<octave>[0-9]+)$", re.IGNORECASE)
    pitch_class = None
    octave = None
    transposition = None
    midi_pitch = None

    def __init__(self, name):
        """Get a pitch by name

        Example pitch names:
            c4 as3 bes2 cis5 f8 eses3

        """
        # Parse the given name
        # It helps to lowercase everything on the way in...
        match = self.name_regex.match(name)
        if not match:
            raise ValueError("Invalid pitch name")
        self.pitch_class = match.group('class').lower()
        self.octave = int(match.group('octave'))
        accidentals = match.group('accidentals').lower()
        flats = accidentals.count('es') + accidentals.count('b')
        sharps = accidentals.count('is') + accidentals.count('#')
        self.transposition = sharps - flats
        # Catch the special cases of 'as' and 'es' (one extra flat)
        if self.pitch_class == 'as' or self.pitch_class == 'es':
            self.transposition -= 1
            self.pitch_class = self.pitch_class[:-1]

    def __repr__(self):
        return "Pitch('" + self.name + "')"

    def __str__(self):
        """Print a more human-friendly representation of the pitch

        This is WRONG; it should find double-sharps and double-flats and
        use the appropriate characters! Probably there should be an external
        function that converts a transposition to the correct sharps/flats.
        It could also convert a string.

        """
        if self.transposition > 0:
            # Sharps
            accidentals = "\u266F" * self.transposition
            # accidentals = "#" * self.transposition
        elif self.transposition < 0:
            # Flats
            accidentals = "\u266D" * (-1 * self.transposition)
            # accidentals = "b" * (-1 * self.transposition)
        else:
            accidentals = ""
        return self.pitch_class.upper() + accidentals + str(self.octave)

    @property
    def name(self):
        pitch_class = self.pitch_class
        octave = self.octave
        transposition = self.transposition
        if transposition < 0 and (pitch_class == 'a' or pitch_class == 'e'):
            pitch_class += 's'
            transposition += 1
        if transposition > 0:
            accidentals = ['is'] * transposition
        elif transposition < 0:
            accidentals = ['es'] * (-1 * transposition)
        else:
            accidentals = []
        return pitch_class + "".join(accidentals) + str(octave)

    @property
    def frequency(self):
        return 440.0 * (2 ** ((self.midi_pitch - 69) / 12))

class Interval:
    """Represents the distance between two pitches

    """
    name_regex = re.compile(r"(?P<quality>[AMmd])(P<interval>[1-9][0-9]*)")

    def __init__(self, name):
        match = self.name_regex.match(name)
        if match:
            self._quality = match.group(1)
            self._generic = match.group(2)
        else:
            raise ValueError()
