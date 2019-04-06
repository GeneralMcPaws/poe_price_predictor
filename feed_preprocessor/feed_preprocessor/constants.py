from enum import Enum
import re

class Constant:
    
    LINE_REGEX= re.compile(r'''([a-zA-Z ,']*)([-+]?\(\d+-\d+\)-\(\d+-\d+\)|[-+]?\(?-?\d+\.?\d*[-+]?\d?\.?\d*\)? to [-+]?\(?-?\d+\.?\d*[-+]?\d?\.?\d*\)?|[-+]?\(?-?\d+\.?\d*[-+]?\d?\.?\d*\)?)(%?[a-zA-Z ,']*)(\(\d+-\d+\)-\(\d+-\d+\)|\(?\d+\.?\d*[-+]?\d?\.?\d*\)?)?(%?[a-zA-Z ,']*)(\(\d+-\d+\)-\(\d+-\d+\)|\(?\d+\.?\d*[-+]?\d?\.?\d*\)? to \(?\d+\.?\d*[-+]?\d?\.?\d*\)?%?|\(?\d+\.?\d*[-+]?\d?\.?\d*\)?)?(%?)''')

    FILENAME = 'poestash2.json'

    PRICE_REGEX = re.compile(r'~(price|b\/o) (\d*.?\d*) (\w+-?\w*)')
    WEAPONS_REGEX = re.compile(r'(one|two)\w+')
    ITEM_NAME_REGEX = re.compile(r'<<set:MS>><<set:M>><<set:S>>(.*)')
    PERCENTAGE_REGEX= re.compile(r'\+?(\d+\.?\d*)%?')
    DAMAGE_REGEX = re.compile(r'\+?(\d+\.?\d*)%?')
    DATE_TIME_COUNT_REGEX = re.compile(r'(\d{4})-(\d{2})-(\d{2})-(\d{2})-(\d{2})-(\d+)')


class Rarity(Enum):
	NORMAL = 0
	MAGIC = 1
	RARE = 2
	UNIQUE = 3
