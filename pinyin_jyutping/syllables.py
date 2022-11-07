from . import logic
from . import constants
import functools


class PinyinSyllable():
    def __init__(self, initial, final, tone, capital=False):
        self.initial = initial
        self.final = final
        self.tone = tone
        self.capital=capital

    def render_tone_mark(self):
        # special case for 'er'
        if self.initial == constants.PinyinInitials.empty:
            return f'{logic.apply_tone_mark(self.final, self.tone)}'
        return f'{self.initial.name}{logic.apply_tone_mark(self.final, self.tone)}'

    def render_tone_number(self):
        if self.initial == constants.PinyinInitials.empty:
            return f'{self.final.name}{self.tone.tone_number}'
        return f'{self.initial.name}{self.final.name}{self.tone.tone_number}'

    def __repr__(self):
        return f'{self.initial.name}{self.final.name}{self.tone.tone_number}'

    def __str__(self):
        return self.render_tone_number()

    def __eq__(self, other):
        if other == None:
            return False
        return self.initial == other.initial and \
               self.final == other.final and \
               self.tone == other.tone and \
               self.capital == other.capital


@functools.lru_cache(maxsize=None)
def build_pinyin_syllable(initial, final, tone, capital):
    return PinyinSyllable(initial, final, tone, capital=capital)