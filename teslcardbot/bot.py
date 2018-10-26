import requests
import random
import json
import praw
import re
import os

from prawcore.exceptions import PrawcoreException

import praw.exceptions


def remove_duplicates(seq):
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]


class Card:
    CARD_IMAGE_BASE_URL = 'http://www.legends-decks.com/img_cards/{}.png'
    CARD_IMAGE_404_URL = 'http://imgur.com/1Lxy3DA'
    JSON_DATA = []
    KEYWORDS = ['Prophecy', 'Breakthrough', 'Guard', 'Regenerate', 'Charge',
                'Ward', 'Shackle',
                'Lethal', 'Pilfer', 'Last Gasp', 'Summon', 'Drain', 'Assemble',
                'Betray',
                'Exalt', 'Plot', 'Rally', 'Slay', 'Treasure Hunt']
    PARTIAL_MATCH_END_LENGTH = 20

    @staticmethod
    def preload_card_data(path='data/cards.json'):
        dir = os.path.dirname(__file__)
        filename = os.path.join(dir, path)

        with open(filename) as f:
            Card.JSON_DATA = json.load(f)

    @staticmethod
    def _escape_name(card):
        return re.sub(r'[\s_\-"\',;{\}]', '', card).lower()

    @staticmethod
    def _img_exists(url):
        req = requests.get(url)
        return req.headers['content-type'] == 'image/png'

    @staticmethod
    def _extract_keywords(text):
        expr = re.compile(r'((?<!Gasp:\s)\w+(?:\sGasp)?)', re.I)
        # If the card is an item, remove the +x/+y from its text.
        text = re.sub(r'\+\d/\+\d', '', text)
        words = expr.findall(text)
        # Keywords are extracted until a non-keyword word is found
        keywords = []
        for word in words:
            word = word.title()
            if word in Card.KEYWORDS:
                keywords.append(word)
            else:
                break
        return remove_duplicates(keywords)

    @staticmethod
    def _get_bigrams(word):
        bigrams = []
        for i in range(len(word) - 1):
            bigrams.append(word[i:i + 2])
        return bigrams

    @staticmethod
    def _get_union(list1, list2):
        return list(set(list1 + list2))

    @staticmethod
    def _get_intersection(list1, list2):
        return [x for x in list1 if x in list2]

    @staticmethod
    def _get_similarity_index(word1, word2):
        bigrams1 = Card._get_bigrams(word1)
        bigrams2 = Card._get_bigrams(word2)
        return len(Card._get_intersection(bigrams1, bigrams2)) / len(
            Card._get_union(bigrams1, bigrams2))

    @staticmethod
    def _get_data_with_typo(name):
        """
        This function implements spell-checking algorithm using bigrams.
        The idea is simple: we get all the bigrams for the input word and every
        word from the dictionary to see how closely they match, and return
        the closest matching card. We determine how close the match is by
        checking the relation of lengths of intersection of bigram lists to
        their intersection
        Example:
        Jeral and Jerall are 2 words we are checking
        For the first one, the bigrams would be ['je', 'er', 'ra', 'al'],
        for the second one: ['je', 'er', 'ra', 'al' ,''ll]
        Length of union is 5, length of intersection is 4, so similarity index
        is 4/5 or 0.8, so it's likely to be the same word with a typo
        Ex.2: Jerall and Jeroll:
        For the first one, the bigrams would be ['je', 'er', 'ra', 'al', 'll'],
        for the second one: ['je', 'er', 'ro', 'ol' ,''ll]
        Union is of length 7, union is of length 3, so the index is 3/7 or
        approx. 0.43. Still quite good, and probably will be the best bet.
        :param name: the name of the card we are trying to find
        :return: the card with the best match and the index
        """
        best_match = None
        best_similarity = 0
        all_sims = []
        for x in Card.JSON_DATA:
            ind = Card._get_similarity_index(Card._escape_name(name),
                                             Card._escape_name(x['name']))
            all_sims.append(ind)
            if ind > best_similarity:
                best_match = x
                best_similarity = ind
            elif ind == best_similarity and best_match is not None:
                # if we met a collision, we check corresponding letters in each word
                prev_matching_letters = 0
                new_matching_letters = 0
                for i in range(min(len(name), len(x['name']), len(best_match['name']))):
                    if x['name'][i] == name[i]:
                        new_matching_letters += 1
                    if best_match['name'][i] == name[i]:
                        prev_matching_letters += 1
                # if the new match has more similarities in letter order than the previous one,
                # or if letter order is similar, but the length of the second one is closer to the query,
                # we assume the new one is the correct one
                if new_matching_letters > prev_matching_letters or \
                    new_matching_letters == prev_matching_letters and \
                        abs(len(name) - len(x['name'])) < abs(len(name) - len(best_match['name'])):
                    best_match = x
                    best_similarity = ind
        return [best_match], best_similarity

    @staticmethod
    def _fetch_data_partial(name):
        i = 0
        matches = ['', '']
        while len(matches) > 1 and i <= Card.PARTIAL_MATCH_END_LENGTH:
            matches = [s for s in Card.JSON_DATA if
                       Card._escape_name(name[:i]) in Card._escape_name(
                           s['name'])]
            i += 1

        res = []
        for match in matches:
            if Card._escape_name(name) in Card._escape_name(match['name']):
                res.append(match)
        return res

    @staticmethod
    def get_info(name):
        name = Card._escape_name(name)
        index = 1  # will need it later, I'll explain why
        if name == 'teslcardbot':  # I wonder...
            return Card('TESLCardBot',
                        'https://imgs.xkcd.com/comics/tabletop_roleplaying.png',
                        type='Bot',
                        attributes='Python/JSON',
                        rarity='Legendary',
                        text='If your have more health than your opponent, win the game.',
                        cost='∞', power='∞', health='∞')

        # If JSON_DATA hasn't been populated yet, try to do it now or fail miserably.
        if len(Card.JSON_DATA) <= 0:
            Card.preload_card_data()
            assert (len(Card.JSON_DATA) > 0)

        data = Card._fetch_data_partial(name)

	# We handle some common card nicknames here	
        if 'tazdaddy' in name.lower():
            name = 'tazkad the packmaster'
        if 'dangernoodle' in name.lower():
            name = 'giant bat'
        if 'bonedaddy' in name.lower():
            name = 'bone colossus'
		
        if not data:
            # Attempting to guess a card that is written with a typo
            data, index = Card._get_data_with_typo(name)

        if data[0] is None or index < 0.28:
            # if we found literally nothing (which is unlikely), or they aren't similar enough, quit
            # 0.25 is chosen from the top of my head, may need tweaking
            return None
        res = []
        for card in data:
            img_url = Card.CARD_IMAGE_BASE_URL.format(
                Card._escape_name(card['name']))
            # Unlikely, but possible?
            if not Card._img_exists(img_url):
                img_url = Card.CARD_IMAGE_404_URL
    
            name = card['name']
            type = card['type']
            attributes = card['attributes']
            rarity = card['rarity']
            unique = card['isunique'] == True
            cost = int(card['cost'])
			
	    # change cost to unicode circled number
            unicodeNumbers = ["⓿","❶","❷","❸","❹","❺","❻","❼","❽","❾","❶⓿","❶❶","❶❷","⑬","⑭","⑮","⑯","⑰","⑱","⑲","❷⓿"]
            cost = unicodeNumbers[cost]

            text = card['text']
            power = ''
            health = ''
            if type == 'creature':
                power = int(card['attack'])
                health = int(card['health'])
            elif type == 'item':
                # Stats granted by items are extracted from their text
                stats = re.findall(r'\+(\d)/\+(\d)', text)
                power, health = stats[0]
            else:
                stats = None
				
            res.append(Card(name=name,
                        img_url=img_url,
                        type=type,
                        attributes=attributes,
                        rarity=rarity,
                        unique=unique,
                        cost=cost,
                        power=power,
                        health=health,
                        text=text))
        return res

    def __init__(self, name, img_url, type='Creature', attributes='neutral', text='', rarity='Common', unique=False, cost=0, power=0, health=0):
        self.name = name
        self.img_url = img_url
        self.type = type
        self.attributes = attributes
        self.rarity = rarity
        self.unique = unique
        self.cost = cost
        self.power = power
        self.health = health
        self.text = text
        self.keywords = Card._extract_keywords(text)

    def __str__(self):
        template = ' **[{name}]({url})** ' \
                   '| {stats} {type} |  {mana} | {keywords} | {attrs} | {unique}{rarity} | {text}'

        def _format_stats(t):
            if self.type == 'creature':
                return t.format('{}/'.format(self.power), '{}'.format(self.health))
            elif self.type == 'item':
                return t.format('+{}/'.format(self.power),
                                '+{}'.format(self.health))
            else:
                return t.format('','')

        return template.format(
            attrs=self.attributes,
            unique='' if not self.unique else 'Unique ',
            rarity=self.rarity.title(),
            name=self.name,
            url=self.img_url,
            type=self.type.title(),
            mana=self.cost,
            stats=_format_stats('{}{}'),
            keywords=', '.join(map(str, self.keywords)) + '' if len(
                self.keywords) > 0 else 'None',
            text=self.text if len(self.text) > 0 else 'This card has no text.'
        )

class TESLCardBot:
    # Using new regex that doesn't match {{}} with no text or less than 3 chars.
    CARD_MENTION_REGEX = re.compile(r'\{\{([ ]*[A-Za-z-\']{3,}[A-Za-z ]*)\}\}')

    @staticmethod
    def find_card_mentions(s):
        return remove_duplicates(TESLCardBot.CARD_MENTION_REGEX.findall(s))

    def _get_praw_instance(self):
        r = praw.Reddit(client_id=os.environ['CLIENT_ID'],
                        client_secret=os.environ['CLIENT_SECRET'],
                        user_agent='Python TESL Bot 9000.01 u/tesl-bot-9000',
                        username=os.environ['REDDIT_USERNAME'],
                        password=os.environ['REDDIT_PASSWORD'])
        return r

    def _process_submission(self, s):
        cards = TESLCardBot.find_card_mentions(s.selftext)
        if len(cards) > 0 and not s.saved:
            try:
                self.log('Commenting in post by {} titled "{}" about the following cards: {}'.format(s.author, s.title, cards))
                response = self.build_response(cards)
                s.reply(response)
                s.save()
                self.log('Done commenting and saved thread.')
            except:
                self.log('There was an error while trying to leave a comment.')
                raise

    def _process_comment(self, c):
        cards = TESLCardBot.find_card_mentions(c.body)
        if len(cards) > 0 and not c.saved and c.author != os.environ['REDDIT_USERNAME']:
            try:
                self.log('Replying to {} in comment id {} about the following cards: {}'.format(c.author, c.id, cards))
                response = self.build_response(cards)
                c.reply(response)
                c.save()
                self.log('Done replying and saved comment.')
            except:
                self.log('There was an error while trying to reply.')
                raise

    # TODO: Make this template-able, maybe?
    def build_response(self, cards):
        response = ' **Name** | **Type** | **Cost** | **Keywords** | **Attribute** | ' \
                   '**Rarity** | **Text** \n:--:|:--:|:--:|:--:|:--:|:--:|--|--\n'
        too_long = None
        cards_not_found = []
        cards_not_sure = {}
        card_quantity = 0
        cards_found = 0
				  
        for name in cards:
            cards = Card.get_info(name)
            if cards is None:
                cards_not_found.append(name)
                card_quantity += 1
            else:
                card_quantity += 1
                too_long = False
                if len(cards) > 5: # just making sure the comment isn't too long
                    cards_found = int(len(cards)) - 5
                    cards = cards[:5]
                    too_long = True
                for card in cards:
                    response += '{}\n'.format(str(card))
                    # this should mean there was a typo in the input
                    if Card._escape_name(name) not in Card._escape_name(card.name):
                        cards_not_sure[name] = card

        if too_long == True:
            response += '\n Your query matched with too many cards. {} further results were omitted. Could you be more specific please?\n'.format(cards_found)
        if len(cards_not_found) == card_quantity:
            response = 'I\'m sorry, but none of the cards you mentioned were matched. ' \
                       'Tokens and other generated cards may be included soon.\n'
        elif len(cards_not_found) > 0:
            response += '\nOne or more of the cards you mentioned were not matched: _{}._ ' \
                        'Tokens and other generated cards may be included soon.\n'.format(', '.join(cards_not_found))
        if len(cards_not_sure) > 0:
            response += '\nSome of the cards may have been written with typos, but I tried to guess them anyway. ' \
                        'Did I guess these correctly?\n'
            for k in cards_not_sure:
                response += '\n- {} is interpreted as {}\n'.format(k,cards_not_sure[k].name)
        response += '\n\n\n^(_I am a bot, and this action was performed automatically. Created by user G3Kappa. ' \
                    'Maintained by NotGooseFromTopGun. ' \
                    'Special thanks to Jeremy at legends-decks._)' \
                    '\n\n[^Source ^Code](https://github.com/jrwhitehead/TESLCardBot/) ^| [^Send ^PM](https://www.reddit.com/' \
                    'message/compose/?to={})'.format(self.author)
        return response

    def log(self, msg):
        print('tesl-bot-9000 # {}'.format(msg))

    def start(self, batch_limit=10, buffer_size=1000):
        r = None
        try:
            r = self._get_praw_instance()

        except PrawcoreException as e:
            self.log('Reddit seems to be down! Aborting.')
            self.log(e)
            return

        already_done = []
        subreddit = r.subreddit(self.target_sub)

        while True:
            try:
		# Updated the method of acquiring comments and submission as new submissions were not being caught
		# Method from here: https://www.reddit.com/r/redditdev/comments/7vj6ox/can_i_do_other_things_with_praw_while_reading/dtszfzb/?context=3
                new_submissions = r.subreddit(self.target_sub).stream.submissions(pause_after=-1) 
                new_comments = r.subreddit(self.target_sub).stream.comments(pause_after=-1)

            except PrawcoreException as e:
                self.log('Reddit seems to be down! Aborting.')
                self.log(e)
                return

            for s in new_submissions:
                if s is None:
                    break
                self._process_submission(s)
                # The bot will also save submissions it replies to to prevent double-posting.
                already_done.append(s.id)
            for c in new_comments:
                if c is None:
                    break
                self._process_comment(c)
                # The bot will also save comments it replies to to prevent double-posting.
                already_done.append(c.id)

            # If we're using too much memory, remove the bottom elements
            if len(already_done) >= buffer_size:
                already_done = already_done[batch_limit:]

    def __init__(self, author='Anonymous', target_sub='all'):
        self.author = author
        self.target_sub = target_sub
