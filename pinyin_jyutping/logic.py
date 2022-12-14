import functools
import logging
import copy

from . import constants
from . import syllables

logger = logging.getLogger(__file__)


@functools.lru_cache(maxsize=None)
def count_vowels(input):
    count = 0
    for char in input:
        if char in constants.ALL_VOWELS:
            count += 1
    return count

@functools.lru_cache(maxsize=None)
def vowel_location(input):
    i = 0
    for char in input:
        if char in constants.ALL_VOWELS:
            return i
        i += 1
    return None



def apply_tone_mark_on_vowel(pinyin_final_final_form, vowel, tone):
    tone_mark_vowel = constants.VowelToneMap[vowel][tone]
    return pinyin_final_final_form.replace(vowel, tone_mark_vowel)

def vowel_for_tone_mark(pinyin_final_final_form):
    # algorithm from https://en.wikipedia.org/wiki/Pinyin#Rules_for_placing_the_tone_mark    
    vowel_count = count_vowels(pinyin_final_final_form)
    if vowel_count == 1:
        location = vowel_location(pinyin_final_final_form)
        return pinyin_final_final_form[location]
    elif vowel_count > 1:
        vowel = 'a'
        if vowel in pinyin_final_final_form:
            return vowel
        vowel = 'e'
        if vowel in pinyin_final_final_form:
            return vowel
        vowel = 'o'
        if 'ou' in pinyin_final_final_form:
            return vowel
        else:
            # second vowel takes the tone mark
            location = vowel_location(pinyin_final_final_form) + 1
            vowel = pinyin_final_final_form[location]
            return vowel
    raise Exception(f'could not find vowel for tone mark, final: {pinyin_final_final_form}')

def apply_tone_mark(pinyin_initial, pinyin_final, tone):
    pinyin_final_final_form = get_final_str(pinyin_initial, pinyin_final)
    vowel = vowel_for_tone_mark(pinyin_final_final_form)
    return apply_tone_mark_on_vowel(pinyin_final_final_form, vowel, tone)


def get_initial_str(initial):
    result = ''
    if initial != constants.PinyinInitials.empty:
        result = initial.name
    return result

def get_final_str(initial, final):
    result = final.final_text()
    if initial == constants.PinyinInitials.empty:
        # apply replacements
        # from https://en.wikipedia.org/wiki/Pinyin_table
        # also: http://www.pinyin.info/rules/initials_finals.html
        if final == constants.PinyinFinals.u:
            result = 'wu'
        elif final == constants.PinyinFinals.ui:
            return 'wei'
        elif final == constants.PinyinFinals.un:
            return 'wen'
        elif final == constants.PinyinFinals.i:
            return 'yi'
        elif final == constants.PinyinFinals.iu:
            return 'you'
        elif final == constants.PinyinFinals.in_:
            return 'yin'
        elif final == constants.PinyinFinals.ing:
            return 'ying'
        elif result[0] == 'i':
            result = 'y' + result[1:]
        elif result[0] == 'u':
            result = 'w' + result[1:]
        elif result[0] == '??':
            result = 'yu' + result[1:]

    jqx_mappings = {
            constants.PinyinFinals.v: 'u',
            constants.PinyinFinals.ve: 'ue',
            constants.PinyinFinals.van: 'uan',
            constants.PinyinFinals.vn: 'un',            
    }
    special_mappings = {
        constants.PinyinInitials.j: jqx_mappings,        
        constants.PinyinInitials.q: jqx_mappings,
        constants.PinyinInitials.x: jqx_mappings
    }
    altered_final = special_mappings.get(initial, {}).get(final, None)
    if altered_final != None:
        return altered_final

    return result

def render_tone_mark(initial, final, tone):
    # logger.warning(f'render_tone_mark {initial} {final}')
    result = f'{get_initial_str(initial)}{apply_tone_mark(initial, final, tone)}'
    return result

def render_tone_number(initial, final, tone, final_variant=None):
    final_str = get_final_str(initial, final)
    if final_variant != None:
        final_str = final_variant
    result = f'{get_initial_str(initial)}{final_str}{tone.tone_number}'
    return result


def valid_combination(initial, final):
    if initial in [ 
        constants.PinyinInitials.j,
        constants.PinyinInitials.q,
        constants.PinyinInitials.x]:
        if final.final_group in [
            constants.PinyinFinalGroup.group_a,
            constants.PinyinFinalGroup.group_u,
        ]:
            return False
    
    if initial in [
        constants.PinyinInitials.g,
        constants.PinyinInitials.k,
        constants.PinyinInitials.h]:
        if final.final_group in [
            constants.PinyinFinalGroup.group_i,
            constants.PinyinFinalGroup.group_v,            
        ]:
            return False

    if initial in [
        constants.PinyinInitials.b,
        constants.PinyinInitials.p,
        constants.PinyinInitials.m,
        constants.PinyinInitials.f]:
        if final.final_group == constants.PinyinFinalGroup.group_u:
            if final == constants.PinyinFinals.u:
                return True
            return False
        if final.final_group in [
            constants.PinyinFinalGroup.group_v
        ]:
            return False


    if initial in [
        constants.PinyinInitials.z,
        constants.PinyinInitials.c,
        constants.PinyinInitials.s,
        constants.PinyinInitials.zh,
        constants.PinyinInitials.ch,
        constants.PinyinInitials.sh,
        constants.PinyinInitials.r
        ]:
        if final.final_group in [
            constants.PinyinFinalGroup.group_i,
            constants.PinyinFinalGroup.group_v
        ]:
            if final == constants.PinyinFinals.i:
                return True
            return False            

    if final == constants.PinyinFinals.er:
        if initial != constants.PinyinInitials.empty:
            return False

    return True

def solution_generator(word_list, solution):
    word_index = 0
    character_index = 0
    for word, word_solution in zip(word_list, solution):
        character_index = 0
        for chinese_character, syllable in zip(word, word_solution):
            yield {
                'word_index': word_index,
                'character_index': character_index,
                'chinese_character': chinese_character,
                'syllable': syllable
            }
            character_index += 1
        word_index += 1

def solution_change_tone(solution, word_index, character_index, new_tone):
    word_copy = copy.copy(solution[word_index])
    syllable_copy = copy.copy(word_copy[character_index]) 
    syllable_copy.tone = new_tone

    word_copy[character_index] = syllable_copy
    solution[word_index] = word_copy    

def apply_pinyin_tone_change(word_list, solution):
    prev_character = None
    for character in solution_generator(word_list, solution):
        if prev_character != None:
            if prev_character['chinese_character'] == '???':
                if character['syllable'].tone == constants.PinyinTones.tone_4:
                    solution_change_tone(solution, prev_character['word_index'], prev_character['character_index'], constants.PinyinTones.tone_2)
            elif prev_character['chinese_character'] == '???':
                if character['syllable'].tone == constants.PinyinTones.tone_4:
                    solution_change_tone(solution, prev_character['word_index'], prev_character['character_index'], constants.PinyinTones.tone_2)
                else:
                    # doesn't seem to be universally applied
                    #solution_change_tone(solution, prev_character['word_index'], prev_character['character_index'], constants.PinyinTones.tone_4)
                    pass


        prev_character = character

    return solution