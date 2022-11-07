import pinyin_jyutping
import pinyin_jyutping.parser
import pinyin_jyutping.data
import pickle
import unittest
import pytest
import pprint
import logging

logger = logging.getLogger(__file__)

from pinyin_jyutping.syllables import PinyinSyllable
from pinyin_jyutping.constants import PinyinInitials, PinyinFinals, PinyinTones

class BuildTests(unittest.TestCase):
    def verify_parsing(self, text, initial, final, tone, tone_mark_render, tone_number_render):
        syllable, remaining_text = pinyin_jyutping.parser.parse_pinyin(text)
        expected_syllable = PinyinSyllable(initial, final, tone)
        self.assertEqual(syllable, expected_syllable)
        self.assertEqual(syllable.render_tone_mark(), tone_mark_render)
        self.assertEqual(syllable.render_tone_number(), tone_number_render)

    def test_parse_pinyin(self):
        text = 'mǎ'
        syllable, remaining_text = pinyin_jyutping.parser.parse_pinyin(text)
        expected_syllable = PinyinSyllable(
            PinyinInitials.m, 
            PinyinFinals.a, 
            PinyinTones.tone_3)
        self.assertEqual(syllable, expected_syllable)
        self.assertEqual(syllable.render_tone_mark(), 'mǎ')
        self.assertEqual(syllable.render_tone_number(), 'ma3')

        text = 'xiē'
        syllable, remaining_text = pinyin_jyutping.parser.parse_pinyin(text)
        expected_syllable = PinyinSyllable(PinyinInitials.x, PinyinFinals.ie, PinyinTones.tone_1)
        self.assertEqual(syllable, expected_syllable)
        self.assertEqual(syllable.render_tone_mark(), 'xiē')
        self.assertEqual(syllable.render_tone_number(), 'xie1')

        text = 'xie1'
        syllable, remaining_text = pinyin_jyutping.parser.parse_pinyin(text)
        self.assertEqual(syllable, expected_syllable)

        self.verify_parsing('nǚ', PinyinInitials.n, PinyinFinals.v, PinyinTones.tone_3, 'nǚ', 'nv3')

    def test_pinyin_parsing_special_cases(self):
        self.verify_parsing('er4', PinyinInitials.empty, PinyinFinals.er, PinyinTones.tone_4, 'èr', 'er4')
        self.verify_parsing('a1', PinyinInitials.empty, PinyinFinals.a, PinyinTones.tone_1, 'ā', 'a1')

    def test_parse_pinyin_word(self):
        text = 'yi1 ge5 ban4'
        expected_output = [
            PinyinSyllable(PinyinInitials.y, PinyinFinals.i, PinyinTones.tone_1),
            PinyinSyllable(PinyinInitials.g, PinyinFinals.e, PinyinTones.tone_neutral),
            PinyinSyllable(PinyinInitials.b, PinyinFinals.an, PinyinTones.tone_4),
        ]
        output = pinyin_jyutping.parser.parse_pinyin_word(text)
        self.assertEqual(output, expected_output)

    def test_parse_pinyin_syllable_list(self):
        text = 'yue4'
        # expected_syllable

    def test_parse_pinyin_word_list(self):
        pass
        # long2 teng2 hu3 yue4

        text = 'long2 teng2 hu3 yue4'
        expected_output = [
            PinyinSyllable(PinyinInitials.l, PinyinFinals.ong, PinyinTones.tone_2),
            PinyinSyllable(PinyinInitials.t, PinyinFinals.eng, PinyinTones.tone_2),
            PinyinSyllable(PinyinInitials.h, PinyinFinals.u, PinyinTones.tone_3),
            PinyinSyllable(PinyinInitials.y, PinyinFinals.u, PinyinTones.tone_3),
        ]
        output = pinyin_jyutping.parser.parse_pinyin_word(text)
        self.assertEqual(output, expected_output)        


    def test_parse_pinyin_word_capitalized(self):
        text = 'Long2 feng4'
        expected_output = [
            PinyinSyllable(PinyinInitials.l, PinyinFinals.ong, PinyinTones.tone_2, capital=True),
            PinyinSyllable(PinyinInitials.f, PinyinFinals.eng, PinyinTones.tone_4),
        ]
        output = pinyin_jyutping.parser.parse_pinyin_word(text)
        self.assertEqual(output, expected_output)


    def test_parse_cedict(self):
        line = '上周 上周 [shang4 zhou1] /last week/'
        simplified, traditional, syllables = pinyin_jyutping.parser.parse_cedict_line(line)
        self.assertEqual(simplified, '上周')
        self.assertEqual(traditional, '上周')
        self.assertEqual(syllables, [
            PinyinSyllable(PinyinInitials.sh, PinyinFinals.ang, PinyinTones.tone_4),
            PinyinSyllable(PinyinInitials.zh, PinyinFinals.ou, PinyinTones.tone_1),            
        ])

    def test_build_data_cedict(self):
        data = pinyin_jyutping.data.Data()
        lines = [
            '誰 谁 [shei2] /who/also pr. [shui2]/',
            '誰知 谁知 [shei2 zhi1] /who would have thought/unexpectedly/',
            '阿誰 阿谁 [a1 shui2] /who/',
            '不准 不准 [bu4 zhun3] /not to allow/to forbid/to prohibit/'
        ]
        pinyin_jyutping.parser.parse_cedict_entries(lines, data)

        # pprint.pprint(data)
        self.assertEqual(len(data.character_map['谁']), 2)

        # check first character mapping
        character_mapping_1 = data.character_map['谁'][0]
        self.assertEqual(character_mapping_1.syllable, 
            PinyinSyllable(PinyinInitials.sh, PinyinFinals.ei, PinyinTones.tone_2),)
        self.assertEqual(character_mapping_1.occurences, 2)

        # check second character mapping
        character_mapping_2 = data.character_map['谁'][1]
        self.assertEqual(character_mapping_2.syllable, 
            PinyinSyllable(PinyinInitials.sh, PinyinFinals.ui, PinyinTones.tone_2),)
        self.assertEqual(character_mapping_2.occurences, 1)

        # check word
        self.assertEqual(len(data.word_map['不准']), 1)
        self.assertEqual(data.word_map['不准'][0].syllables,
        [
            PinyinSyllable(PinyinInitials.b, PinyinFinals.u, PinyinTones.tone_4),
            PinyinSyllable(PinyinInitials.zh, PinyinFinals.un, PinyinTones.tone_3)
        ]
        )

    def test_build_data_cedict_ordering(self):
        data = pinyin_jyutping.data.Data()
        lines = [
            '誰 谁 [shei2] /who/also pr. [shui2]/',
            '誰 谁 [shei2] /test 1/',
            '誰 谁 [shui2] /test 2/',
            '誰 谁 [shui2] /test 3/',
            '誰 谁 [shui2] /test 4/',
        ]
        pinyin_jyutping.parser.parse_cedict_entries(lines, data)

        # pprint.pprint(data)
        self.assertEqual(len(data.character_map['谁']), 2)

        # check first character mapping
        character_mapping_1 = data.character_map['谁'][0]
        self.assertEqual(character_mapping_1.syllable, 
            PinyinSyllable(PinyinInitials.sh, PinyinFinals.ui, PinyinTones.tone_2),)
        self.assertEqual(character_mapping_1.occurences, 3)

        # check second character mapping
        character_mapping_2 = data.character_map['谁'][1]
        self.assertEqual(character_mapping_2.syllable, 
            PinyinSyllable(PinyinInitials.sh, PinyinFinals.ei, PinyinTones.tone_2),)
        self.assertEqual(character_mapping_2.occurences, 2)


    @pytest.mark.skip(reason="a bit slow")
    def test_load_cedict(self):
        data = pinyin_jyutping.data.Data()
        filename = 'source_data/cedict_1_0_ts_utf-8_mdbg.txt'
        pinyin_jyutping.parser.parse_cedict(filename, data)

        self.assertIn('上周', data.simplified_map.word_map)
        self.assertEqual(len(data.simplified_map.word_map['上周']), 1)
        self.assertEqual(data.simplified_map.word_map['上周'][0].syllables,
            [ 
                PinyinSyllable(PinyinInitials.sh, PinyinFinals.ang, PinyinTones.tone_4),
                PinyinSyllable(PinyinInitials.zh, PinyinFinals.ou, PinyinTones.tone_1)
            ]
        )


    def test_dump_load_pickle(self):
        data = pinyin_jyutping.data.Data()
        lines = [
            '上周 上周 [shang4 zhou1] /last week/',
            '誰 谁 [shei2] /who/also pr. [shui2]/',
            '誰知 谁知 [shei2 zhi1] /who would have thought/unexpectedly/',
            '阿誰 阿谁 [a1 shui2] /who/',
            '不准 不准 [bu4 zhun3] /not to allow/to forbid/to prohibit/'
        ]
        pinyin_jyutping.parser.parse_cedict_entries(lines, data)

        pickled_data = pickle.dumps(data)

        unpickled_data = pickle.loads(pickled_data)


    @pytest.mark.skip(reason="still experimenting with pickle")
    def test_save_pickle(self):
        data = pinyin_jyutping.data.Data()
        sample_data_only = False
        if sample_data_only:
            lines = [
                '誰 谁 [shei2] /who/also pr. [shui2]/',
                '誰知 谁知 [shei2 zhi1] /who would have thought/unexpectedly/',
                '阿誰 阿谁 [a1 shui2] /who/',
                '不准 不准 [bu4 zhun3] /not to allow/to forbid/to prohibit/'
            ]
            pinyin_jyutping.parser.parse_cedict_entries(lines, data)
        else:
            filename = 'source_data/cedict_1_0_ts_utf-8_mdbg.txt'
            pinyin_jyutping.parser.parse_cedict(filename, data)            
        data_file = open('pinyin.pkl', 'wb')
        pickle.dump(data, data_file)
        data_file.close()
    
    @pytest.mark.skip(reason="still experimenting with pickle")
    def test_load_pickle(self):
        data_file = open('pinyin.pkl', 'rb')
        data = pickle.load(data_file)
        data_file.close()


    def test_verify_parse_output_pinyin(self):
        """parse all of cedict, and make sure we can faithfully output the pinyin"""
        filename = 'source_data/cedict_1_0_ts_utf-8_mdbg.txt'
        generator = pinyin_jyutping.parser.parse_cedict_file_generator(filename)
        for line in generator:
            traditional_chinese, simplified_chinese, pinyin, definition = pinyin_jyutping.parser.unpack_cedict_line(line)
            try:
                syllables = pinyin_jyutping.parser.parse_pinyin_word(pinyin)
            except pinyin_jyutping.errors.PinyinParsingError as e:
                logger.error(f'while parsing line: [{line}] error: {e}')



if __name__ == '__main__':
    pass