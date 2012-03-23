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
    FLAT_CHAR = 'b'
    SHARP_CHAR = '#'

    __slots__ = ('base_pitch_id', 'octave', 'transposition')

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
        return self.equals(other)

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
        """
        >>> Pitch('a4') + Interval('A3')
        Pitch('c##5')
        >>> Pitch('c4') + Interval('-P8')
        Pitch('c3')
        >>> Pitch('b#0') + Interval('-P8')
        Pitch('b#-1')
        """
        if isinstance(other, Interval):
            if other.descending:
                new_base_pitch_id = self.base_pitch_id - other.generic
            else:
                new_base_pitch_id = self.base_pitch_id + other.generic
            new_pitch = Pitch(base_pitch_id=new_base_pitch_id)
            # Now check the interval transposition
            i = new_pitch - self
            if other.descending:
                new_transposition = other.transposition + i.transposition
            else:
                new_transposition = other.transposition - i.transposition
            return Pitch(base_pitch_id=new_base_pitch_id,
                         transposition=new_transposition)
        else:
            raise NotImplemented("Second operand must be an Interval")

    def __sub__(self, other):
        if isinstance(other, Pitch):
            return Interval(pitches=(other, self))
        elif isinstance(other, Interval):
            return self.__add__(-other)

    def __repr__(self):
        return "Pitch('" + self.name + "')"

    def duplicate(self):
        """
        >>> p = Pitch('ges4')
        >>> d = p.duplicate()
        >>> d == p
        True
        >>> d is p
        False
        """
        return Pitch(base_pitch_id=self.base_pitch_id,
                     transposition=self.transposition)

    def equals(self, other, check_octave=True):
        """
        >>> Pitch('dis4').equals(Pitch('dis7'))
        False
        >>> Pitch('dis4').equals(Pitch('dis7'), check_octave=False)
        True
        >>> Pitch('dis4').equals(Pitch('d4'))
        False
        """
        return (self.pitch_class == other.pitch_class and
                self.transposition == other.transposition and
                (self.octave == other.octave or not check_octave))

    def is_enharmonic(self, other):
        """
        >>> Pitch('c4').is_enharmonic(Pitch('deses4'))
        True
        >>> Pitch('c4').is_enharmonic(Pitch('bis4'))
        False
        >>> Pitch('c4').is_enharmonic(Pitch('bis3'))
        True
        """
        return self.midi == other.midi

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

    NAME_REGEX = re.compile(r"(?P<direction>[+-]?)"
                            r"(?P<quality>(?:d)*|(?:A)*|[PMm])"
                            r"(?P<generic>[1-9][0-9]*)")
    ASCENDING_CHAR = '+'
    DESCENDING_CHAR = '-'

    __slots__ = ('descending', 'generic', 'transposition')

    def __init__(self, name=None, *, pitches=None, generic=None,
                 transposition=None, descending=False):
        if name:
            (self.generic,
             self.transposition,
             self.descending) = Interval.parse_interval_name(name)
        elif pitches:
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
            self.transposition = actual_semitones - (size[simple_generic] +
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
        qm = {-2: 'd', -1: 'm', 0: 'M', 1: 'A'}
        qp = {-1: 'd', 0: 'P', 1: 'A'}
        if Interval.is_perfect_interval(self.generic):
            if self.transposition in qp:
                quality = qp[self.transposition]
            else:
                if self.transposition < 0:
                    quality = "d" * (-1 * self.transposition)
                else:
                    quality = "A" * self.transposition
        else:
            if self.transposition in qm:
                quality = qm[self.transposition]
            else:
                if self.transposition < 0:
                    quality = "d" * (-1 * self.transposition - 1)
                else:
                    quality = "A" * self.transposition
        if self.descending:
            direction = Interval.DESCENDING_CHAR
        else:
            direction = Interval.ASCENDING_CHAR
        return direction + quality + str(self.generic + 1)

    def __copy__(self):
        return Interval(self.name)

    def __neg__(self):
        i = self.__copy__()
        i.descending = not i.descending
        return i

    def __repr__(self):
        return "Interval({!r})".format(self.name)

    @staticmethod
    def is_perfect_interval(generic):
        return generic % 7 in [0, 3, 4]

    @staticmethod
    def parse_interval_name(name):
        match = Interval.NAME_REGEX.match(name)
        if not match:
            raise ValueError("Invalid interval name")
        generic = int(match.group('generic')) - 1
        is_perfect = Interval.is_perfect_interval(generic)
        transposition = Interval.quality_to_transposition(match.group('quality'),
                                                          is_perfect)
        direction = match.group('direction')
        descending = (direction == '-')
        return (generic, transposition, descending)

    @staticmethod
    def quality_to_transposition(quality, is_perfect_interval=False):
        quality_modified = quality + 'p' if is_perfect_interval else quality
        transposition = {'dd': -3, 'd': -2, 'm': -1, 'M': 0, 'A': 1, 'AA': 2,
                         'ddp': -2, 'dp': -1, 'Pp': 0, 'Ap': 1, 'AAp': 2}
        try:
            return transposition[quality_modified]
        except KeyError:
            if is_perfect_interval:
                raise ValueError("{!r} is an invalid quality for a perfect "
                                 "interval".format(quality))
            else:
                raise ValueError("{!r} is an invalid quality for an imperfect "
                                 "interval".format(quality))


class MajorScale:

    intervals = list(map(Interval, 'P1 M2 M3 P4 P5 M6 M7'.split()))

    def __init__(self, start_pitch):
        self.pitches = []
        for interval in MajorScale.intervals:
            self.pitches.append(start_pitch + interval)

    def is_diatonic(self, pitch):
        """
        >>> MajorScale(Pitch('c4')).is_diatonic(Pitch('d5'))
        True
        >>> MajorScale(Pitch('b0')).is_diatonic(Pitch('ais7'))
        True
        >>> MajorScale(Pitch('c4')).is_diatonic(Pitch('eis3'))
        False
        """
        for p in self.pitches:
            if pitch.equals(p, check_octave=False):
                return True
        return False


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
