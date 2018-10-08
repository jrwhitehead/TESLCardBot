import unittest
from teslcardbot.bot import TESLCardBot, Card


class TestParsingFunctions(unittest.TestCase):

    def setUp(self):
        self.bot = TESLCardBot(author='tesl-bot-9000', target_sub='jrwBotTesting')
        Card.preload_card_data()

    def test_find_card_mentions(self):
        # Make sure the basic functioning works
        self.assertEqual(TESLCardBot.find_card_mentions('{{Test}}'), ['Test'])
        self.assertEqual(TESLCardBot.find_card_mentions('{{Test}} {{Blood Dragon}}'), ['Test', 'Blood Dragon'])
        # Make sure the repetition avoidance works
        self.assertEqual(TESLCardBot.find_card_mentions('{{Test}} {{Blood Dragon}} ' * 4), ['Test', 'Blood Dragon'])

    def test_escape_card_name(self):
        self.assertEqual(Card._escape_name('Blood Dragon'), 'blooddragon')
        self.assertEqual(Card._escape_name('Bl-ood, _-"\' Drag;on'), 'blooddragon')
        self.assertEqual(Card._escape_name('{{{HOHO}}}}}'), 'hoho')

    def test_extract_keywords(self):
        self.assertEqual(Card._extract_keywords('Charge'),['Charge'])
        self.assertEqual(Card._extract_keywords('Charge, Pilfer'),['Charge', 'Pilfer'])
        self.assertEqual(Card._extract_keywords('cHaRge. dRaIn'),['Charge', 'Drain'])
        self.assertEqual(Card._extract_keywords('Summon: Ayy lmao'),['Summon'])
        self.assertEqual(Card._extract_keywords('+4/+4 Summon: Destroy a bee.'),['Summon'])
        self.assertEqual(Card._extract_keywords('Charge. Last Gasp: rip 2016'),['Charge', 'Last Gasp'])
        self.assertEqual(Card._extract_keywords('Summon: Summon a minion with Guard.'),['Summon'])
        self.assertEqual(Card._extract_keywords('Breakthrough, Charge, Last Gasp: Summon a meme'), ['Breakthrough', 'Charge', 'Last Gasp'])

    def test_fetch_data_partial(self):
        self.assertEqual(Card._fetch_data_partial('tyr')[0]['name'], 'Tyr')
        self.assertEqual(Card._fetch_data_partial('lesser')[0]['name'], 'Lesser Ward')
        self.assertEqual(Card._fetch_data_partial('gortwog')[0]['name'], 'Gortwog gro-Nagorm')
        self.assertEqual(Card._fetch_data_partial('Breton Conjurer')[0]['name'], 'Breton Conjurer')
        self.assertEqual(Card._fetch_data_partial('quinrawl')[0]['name'], 'Quin\'rawl Burglar')

    def test_get_info(self):
        Card.preload_card_data()
        self.maxDiff = None
        print(str(Card.get_info('tyr')))
        # print(str(Card.get_info('lesser ward')))
        print(str(Card.get_info('dawnbreaker')))

        self.assertEqual(str(Card.get_info('tyr')[0]), '[📷](http://www.legends-decks.com/img_cards/tyr.png) Tyr '
                                                    '| Creature | 4 - 5/4 | Prophecy, Breakthrough, Guard '
                                                    '| Strength/Willpower | Unique Legendary | Prophecy, Breakthrough, Guard')

        self.assertEqual(str(Card.get_info('lesser w')[0]), '[📷](http://www.legends-decks.com/img_cards/'
                                                         'lesserward.png) Lesser Ward | Action | 0 - ?/? | None '
                                                         '| Intelligence | Common | Give a creature a Ward.')

        self.assertEqual(str(Card.get_info('dawnb')[0]), '[📷](http://www.legends-decks.com/img_cards/dawnbreaker.png) '
                                                     'Dawnbreaker | Item | 4 - +4/+4 | Summon | Willpower '
                                                     '| Unique Legendary | +4/+4. Summon: Destroy an enemy Undead.')


if __name__ == '__main__':
    unittest.main()
