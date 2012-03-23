from collections import namedtuple
import re

class Pitch:
    """A musical pitch, defined by a pitch class, octave, and transposition

    Pitches by name:
    >>> p = Pitch('a4')
    >>> (p.pitch_class, p.octave)
    ('a', 4)

    Pitches by base_pitch_id:
    >>> p = Pitch(base_pitch_id=0)
    >>> (p.pitch_class, p.octave)
    ('c', 0)
    >>> p = Pitch(base_pitch_id=3)
    >>> (p.pitch_class, p.octave)
    ('f', 0)
    >>> p = Pitch(base_pitch_id=7)
    >>> (p.pitch_class, p.octave)
    ('c', 1)
    >>> p = Pitch(base_pitch_id=33)
    >>> (p.pitch_class, p.octave)
    ('a', 4)

    """
    NAME_REGEX = re.compile('^(?P<base>as|es|[a-g])'
                            '(?P<accidentals>(?:es)*|(?:is)*|b*|#*)'
                            '(?P<octave>[0-9]+)$', re.IGNORECASE)
    FLAT_CHAR = '\u266D'
    SHARP_CHAR = '\u266F'

    def __init__(self, name=None, *, base_pitch_id=None, transposition=None,
                 pitch_class=None, octave=None):
        if isinstance(name, str):
            p = Pitch.parse_pitch_name(name)
            self.base_pitch_id, self.transposition = p
        elif base_pitch_id is not None:
            self.base_pitch_id = base_pitch_id
            if transposition is not None:
                self.transposition = transposition
            else:
                self.transposition = 0
        else:
            raise ValueError("Invalid arguments; give name or base_pitch_id "
                             "and transposition")

    @property
    def frequency(self):
        return 440 * (2 ** ((self.midi - 69) / 12))

    @property
    def midi(self):
        d = {'c': 0, 'd': 2, 'e': 4, 'f': 5, 'g': 7, 'a': 9, 'b': 11}
        return ((self.octave + 1) * 12 +
                d[self.pitch_class] +
                self.transposition)

    @property
    def name(self):
        if self.transposition > 0:
            accidentals = Pitch.SHARP_CHAR * self.transposition
        else:
            accidentals = Pitch.FLAT_CHAR * (-1 * self.transposition)
        return self.pitch_class + accidentals + str(self.octave)

    @property
    def octave(self):
        return self.base_pitch_id // 7

    @property
    def pitch_class(self):
        return list('cdefgab')[self.base_pitch_id % 7]

    def __eq__(self, other):
        return (self.base_pitch_id == other.base_pitch_id and
                self.transposition == other.transposition)

    def __ne__(self, other):
        return self.midi != other.midi

    def __lt__(self, other):
        return self.midi < other.midi

    def __le__(self, other):
        return self.__lt__(other) or self.__eq__(other)

    def __gt__(self, other):
        return not self.__le__(other)

    def __ge__(self, other):
        return not self.__lt__(other)

    def __add__(self, other):
        if isinstance(other, Interval):
            new_base_pitch_id = self.base_pitch_id + other.generic
            new_transposition = self.transposition + other.quality
            new_pitch = Pitch(base_pitch_id=new_base_pitch_id)
            # Now check the interval quality
            i = new_pitch - self
            new_transposition = other.quality - i.quality
            return Pitch(base_pitch_id=new_base_pitch_id,
                         transposition=new_transposition)
        else:
            raise NotImplemented("Second operand must be an Interval")

    def __sub__(self, other):
        if isinstance(other, Pitch):
            return Interval((other, self))
        elif isinstance(other, Interval):
            raise NotImplemented("Intervals can't currently be subtracted "
                                  "from pitches")

    def __repr__(self):
        return "Pitch('" + self.name + "')"

    def duplicate(self):
        """Return a duplicate of self

        >>> p = Pitch('ges4')
        >>> d = p.duplicate()
        >>> d == p
        True
        >>> d is p
        False

        """
        return Pitch(base_pitch_id=self.base_pitch_id,
                     transposition=self.transposition)

    @staticmethod
    def parse_pitch_name(name):
        match = Pitch.NAME_REGEX.match(name)
        if not match:
            raise ValueError("Invalid pitch name")
        accidentals = match.group('accidentals').lower()
        flats = accidentals.count('es') + accidentals.count('b')
        sharps = accidentals.count('is') + accidentals.count('#')
        octave = int(match.group('octave'))
        base_pitch = match.group('base').lower()
        # Catch the two special cases — A-flat and E-flat
        if base_pitch == 'as' or base_pitch == 'es':
            base_pitch = base_pitch[:-1]
            flats += 1
        transposition = sharps - flats
        d = {pitch: id for id, pitch in enumerate(list('cdefgab'))}
        base_pitch_id = octave * 7 + d[base_pitch]
        return (base_pitch_id, transposition)


class Interval:
    """An interval

    """
    NAME_REGEX = re.compile(r"(?P<quality>[AMmd])"
                            r"(?P<interval>[1-9][0-9]*)"
                            r"(?P<direction>[{}{}]?)")
    ASCENDING_CHAR = '\u2191'
    DESCENDING_CHAR = '\u2193'

    def __init__(self, pitches=None, *, generic=None, quality=None,
                 descending=False):
        if pitches:
            from_pitch, to_pitch = pitches
            if from_pitch > to_pitch:
                from_pitch, to_pitch = to_pitch, from_pitch
                self.descending = True
            else:
                self.descending = False
            self.generic = (to_pitch.base_pitch_id -
                            from_pitch.base_pitch_id)
            actual_semitones = to_pitch.midi - from_pitch.midi
            simple_generic = self.generic % 7
            octaves = self.generic // 7
            size = [0, 2, 4, 5, 7, 9, 11]
            self.quality = actual_semitones - (size[simple_generic] +
                                               12 * octaves)

    @property
    def compound(self):
        return self.generic > 7

    @property
    def steps(self):
        size = [0, 2, 4, 5, 7, 9, 11]
        steps = size[self.generic % 7] + (self.generic // 7) * 12
        return steps

    @property
    def name(self):
        perfect_intervals = [0, 3, 4]
        qm = {-2: 'd', -1: 'm', 0: 'M', 1: 'A'}
        qp = {-1: 'd', 0: 'P', 1: 'A'}
        if self.generic % 7 in perfect_intervals:
            if self.quality in qp:
                quality = qp[self.quality]
            else:
                if self.quality < 0:
                    quality = "d" * (-1 * self.quality)
                else:
                    quality = "A" * self.quality
        else:
            if self.quality in qm:
                quality = qm[self.quality]
            else:
                if self.quality < 0:
                    quality = "d" * (-1 * self.quality - 1)
                else:
                    quality = "A" * self.quality
        if self.descending:
            direction = Interval.DESCENDING_CHAR
        else:
            direction = Interval.ASCENDING_CHAR
        return quality + str(self.generic + 1) + direction

    def __repr__(self):
        return "Interval('" + self.name + "')"


class MajorScale:

    intervals = map(Interval, 'P1 M2 M2 m2 M2 M2 M2 m2'.split())

    def __init__(self, start_pitch):
        self.pitches = []
        for interval in self.intervals:
            self.pitches.append(start_pitch + interval)

    def is_diatonic(self, pitch):
        return pitch in self.pitches


if __name__ == '__main__':
    import doctest
    doctest.testmod()
    # Set up some objects for convenient testing
    c3 = Pitch('c3')
    c4 = Pitch('c4')
    d4 = Pitch('d4')
    e4 = Pitch('e4')
    f4 = Pitch('f4')
    g4 = Pitch('g4')
    a4 = Pitch('a4')
    b4 = Pitch('b4')
    c5 = Pitch('c5')
