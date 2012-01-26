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

    You can use "b" for flat and "#" for sharp, but we use the dutch
    names internally.
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
    PITCH_CLASS_VALUES = {
            'c': 0,
            'd': 2,
            'e': 4,
            'f': 5,
            'g': 7,
            'a': 9,
            'b': 11,
        }
    PITCH_CLASS_NAMES = {v:n for n, v in PITCH_CLASS_VALUES.items()}

    def _parse_string(string):
        """Figure out stuff from a pitch name"""
        match = Pitch.name_regex.match(string)
        if not match:
            raise ValueError("Invalid pitch name")
        pitch_class = match.group('class').lower()
        octave = int(match.group('octave'))
        accidentals = match.group('accidentals').lower()
        flats = accidentals.count('es') + accidentals.count('b')
        sharps = accidentals.count('is') + accidentals.count('#')
        transposition = sharps - flats
        # Catch the special cases of 'as' and 'es' (one extra flat)
        if pitch_class == 'as' or pitch_class == 'es':
            transposition -= 1
            pitch_class = pitch_class[:-1]
        return (pitch_class, transposition, octave)

    def _parse_midi_pitch(midi_pitch):
        # Figure out how to get the correct pitch when given a key...
        if midi_pitch % 12 in Pitch.PITCH_CLASS_NAMES:
            pitch_class = Pitch.PITCH_CLASS_NAMES[midi_pitch % 12]
            transposition = 0
        elif midi_pitch % 12 - 1 in Pitch.PITCH_CLASS_NAMES:
            pitch_class = Pitch.PITCH_CLASS_NAMES[midi_pitch % 12 - 1]
            transposition = 1
        octave = midi_pitch // 12 - 1
        return (pitch_class, transposition, octave)

    def __init__(self, value):
        """Get a pitch by name or by midi number

        Example pitch names:
            c4 as3 bes2 cis5 f8 eses3

        """
        if isinstance(value, str):
            parse = Pitch._parse_string
        elif isinstance(value, int):
            parse = Pitch._parse_midi_pitch
        (pc, tr, oc) = parse(value)
        self.pitch_class = pc
        self.transposition = tr
        self.octave = oc

    def __eq__(self, other):
        return self.midi_pitch == other.midi_pitch

    def __ne__(self, other):
        return self.midi_pitch != other.midi_pitch

    def __lt__(self, other):
        return self.midi_pitch < other.midi_pitch

    def __le__(self, other):
        return self.__lt__(other) or self.__eq__(other)

    def __gt__(self, other):
        return not self.__le__(other)

    def __ge__(self, other):
        return not self.__lt__(other)

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

    @property
    def midi_pitch(self):
        return ((self.octave + 1) * 12 +
                Pitch.PITCH_CLASS_VALUES[self.pitch_class] +
                self.transposition)

    def diminish(self, amount):
        pass

    def augment(self, amount):
        pass

class Interval:
    """Represents the distance between two pitches

    """
    name_regex = re.compile(r"(?P<quality>[AMmd])(P<interval>[1-9][0-9]*)")

    def __init__(self, name):
        match = Interval.name_regex.match(name)
        if match:
            self._quality = match.group(1)
            self._generic = match.group(2)
        else:
            raise ValueError()
