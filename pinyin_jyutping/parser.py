import logging
import pprint
import re

from . import constants
from . import syllables
from . import cache
from . import errors

logger = logging.getLogger(__file__)

def parse_pinyin(text):
    # look for initial
    # check first 2 letters
    first_2 = text[0:2]
    cache_hit = cache.PinyinInitialsMap.get(first_2, None)
    if cache_hit != None:
        # special case for 'er'
        if cache_hit == constants.PinyinInitials.er:
            return parse_final_and_tone(cache_hit, text)
        remaining_text = text[2:]
        logger.debug(f'found initial: {first_2}')
        return parse_final_and_tone(cache_hit, remaining_text)
    first_1 = text[0:1]
    cache_hit = cache.PinyinInitialsMap.get(first_1, None)
    if cache_hit != None:
        remaining_text = text[1:]
        logger.debug(f'found initial {first_1}')
        return parse_final_and_tone(cache_hit, remaining_text)
    raise errors.PinyinParsingError(f"couldn't find initial: {text}")

def parse_final_and_tone(initial, text):
    logger.debug(f'looking for final in {text}')
    # pprint.pprint(cache.PinyinFinalsMap)    
    for candidate_length in reversed(range(6)):
        candidate = text[0:candidate_length]
        remaining_text = text[candidate_length:]
        logger.debug(f'scanning for {candidate}, map size: {len(cache.PinyinFinalsMap)}')
        cache_hit = cache.PinyinFinalsMap.get(candidate, None)
        if cache_hit != None:
            final = cache_hit['final']
            tone = cache_hit['tone']
            return syllables.PinyinSyllable(initial, final, tone), remaining_text
    raise errors.PinyinParsingError(f"couldn't find final: {text}")

def parse_pinyin_word(text):
    syllables = []
    while len(text) > 0:
        logger.debug(f'parsing pinyin word: {text}')
        # remove leading space
        text = text.lstrip()
        syllable, text = parse_pinyin(text)
        logger.debug(f'parsed {syllable}, remaining text: {text}')
        syllables.append(syllable)
    return syllables


def parse_cedict(filepath):
    simplified_word_map = {}
    traditional_word_map = {}
    with open(filepath, 'r', encoding="utf8") as filehandle:
        for line in filehandle:
            first_char = line[:1]
            if first_char != '#' and line != "and add boilerplate:\n":
                try:
                    simplified, traditional, syllables = parse_cedict_line(line)
                    simplified_word_map[simplified] = syllables
                    traditional_word_map[traditional] = syllables
                except errors.PinyinParsingError as e:
                    logger.error(e)

    return simplified_word_map, traditional_word_map


def parse_cedict_line(line):
    logger.debug(f'parsing cedict line: {line}')
    m = re.match('([^\s]+)\s([^\s]+)\s\[([^\]]*)\]\s\/([^\/]+)\/.*', line)
    if m == None:
        logger.info(line)
    traditional_chinese = m.group(1)
    simplified_chinese = m.group(2)
    pinyin = m.group(3)
    definition = m.group(4)        
    # parse the pinyin
    syllables = parse_pinyin_word(pinyin)
    return simplified_chinese, traditional_chinese, syllables