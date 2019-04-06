from enum import Enum
import re

class Config:
        
    FILENAME = 'test.txt'
    REGEX_FOLDER_NAME = 'Regex'
    JSON_FOLDER_NAME ='Json'

    #regex for breaking down the line values. Groups 1, 3 and 5 are the groups with numbers
    LINE_REGEX= re.compile(r'''([a-zA-Z ,']*)([-+]?\(\d+-\d+\)-\(\d+-\d+\)|[-+]?\(?-?\d+\.?\d*[-+]?\d?\.?\d*\)? to [-+]?\(?-?\d+\.?\d*[-+]?\d?\.?\d*\)?|[-+]?\(?-?\d+\.?\d*[-+]?\d?\.?\d*\)?)(%?[a-zA-Z ,']*)(\(\d+-\d+\)-\(\d+-\d+\)|\(?\d+\.?\d*[-+]?\d?\.?\d*\)?)?(%?[a-zA-Z ,']*)(\(\d+-\d+\)-\(\d+-\d+\)|\(?\d+\.?\d*[-+]?\d?\.?\d*\)? to \(?\d+\.?\d*[-+]?\d?\.?\d*\)?%?|\(?\d+\.?\d*[-+]?\d?\.?\d*\)?)?(%?)''')

    #regex for checking if a number is ranged or not
    #RANGE_REGEX = re.compile(r'\(\d+-\d+\)-\(\d+-\d+\)|\(\d+\.?\d*[-+]\d+\.?\d*\) to \(\d+\.?\d*[-+]\d+\.?\d*\)|\(\d+\.?\d*[-+]?\d?\.?\d*\)')
    RANGE_REGEX = re.compile(r'\(.*\)')