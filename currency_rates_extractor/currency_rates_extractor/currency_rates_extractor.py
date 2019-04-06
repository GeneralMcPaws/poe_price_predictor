import json,sys,os,io
import argparse
import logging.config
import glob
import time
from pathlib import Path
import csv

parser = argparse.ArgumentParser(description='This program extracts data from processed stashes. ')

group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("-d","--dir",help="Direcotry where data dumps of csv's are",nargs='+')
group.add_argument("-f","--files",help="One or more csv's",nargs='+')
parser.add_argument("-c","--config",help="Configuration file",nargs=1)
parser.add_argument("-lo","--log_level",help="Logging level",nargs=1)
args = parser.parse_args()

if args.config:
    config_file_name = args.config
else:
    config_file_name = 'config.json'


try:
    with io.open(config_file_name,'r') as fjson:
        conf = json.load(fjson)
except Exception as e:
    logging.basicConfig(level=logging.DEBUG,format='%(levelname)s:%(message)s')
    logging.getLogger('file_logger').critical('Critical error -{} - in initializing the configuration of the program. Exiting ...'.format(e))
    quit(0)

if not 'LOGGING' in conf.keys():
    logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:%(message)s')
else:
    logging.config.dictConfig(conf['LOGGING'])

logger = logging.getLogger('file_logger')

if args.log_level:
    logging_level = getattr(logging,args.log_level[0])
    if not isinstance(logging_level,int):
        logger.error('Could not set level of logger to provided {} (not acceptable). Setting log to default : DEBUG'.format(args.log_level[0]))
    else:
        logger.setLevel(logging_level)

logger.info("Starting using configuration file {} ".format(config_file_name))

if not 'CONFIG' in conf.keys():
    logging.getLogger('file_logger').critical('Critical error - Configuration - CONFIG section not found')
    quit(0)

conf = conf['CONFIG']

files_to_process = []

# for option -d : directory or multiple directories as input
if args.dir:

    # for each given directory in the list check if it actually is a directory
    for directory in args.dir:
        data_folder = Path(directory)
        if not data_folder.exists():
            logger.warning('-d  {} is not a directory. Skipping ...'.format(directory))
        file_pattern_search = os.path.join(directory, "*")
        files = list(filter(os.path.isfile, glob.glob(file_pattern_search)))
        files.sort()
        if not files:
            logger.warning('Configuration : {} directory has no files in it'.format(d))
            continue
        for f in files:
            # check if f is a file because glob.glob also returns directories
            if not os.path.isfile(f):
                logger.warning('Configuration : {} is not a file'.format(f))
                continue
            files_to_process.append(f.strip())
   
# for option -f : input give is a file or multiple files
if args.files:
    for f in args.files:
        f = f.strip()
        file = Path(f)
        # check for every file if it is indeed a file
        if not file.exists():
            logger.warning('-f  {} is not a File. Skipping ...'.format(file))
            continue
        files_to_process.append(f)

if not files_to_process:
    logger.critical('Configuration : no files to process! Empty list.')
    quit()

with io.open('abbreviations.json') as fjson:
    try:
        abbreviations = json.load(fjson)
    except Exception as e:
        logger.error("\t\tABBREVIATIONS READ: Could not read abbreviations file with error -{}-".format(e))
        quit()

def process_csv_files(files):

    for file in files:
        try:
            with open(file) as csv_file:
                currency_rates_dictionary = extract_currency_rates(csv_file)
        except Exception as e:
            logger.error("\t\tPROCESS_CSV : error -{}- while processing file : {}".format(e,file))
            continue
        if not currency_rates_dictionary:
            logger.error("\t\tPROCESS_CSV : Could not process csv_file {}".format(file))
            continue
        save_currency_rates_dict(currency_rates_dictionary,file)

def extract_currency_rates(csv_file):
    currency_rates_dictionary = {}
    spamreader = csv.reader(csv_file,delimiter=';')
    #first line is the header, skip that line
    next(spamreader)
    for line in spamreader:
        currency_rates_dictionary = process_csv_line(line,currency_rates_dictionary)
        if not currency_rates_dictionary : return None
    return currency_rates_dictionary



def process_csv_line(line,currency_rates_dictionary):
    league = line[0]
    date = line[1]
    get_currency = line[2]
    give_currency = line[3]
    rate = line[4]

    if date not in currency_rates_dictionary:
        currency_rates_dictionary[date] = {}
    if 'chaos' in get_currency.lower():
        return currency_rates_dictionary
    if get_currency.lower() not in abbreviations:
        return currency_rates_dictionary
    if get_currency in currency_rates_dictionary[date]:
        logger.error("\t\tGET_CURRENCY error : currency -{}- already exists in date -{}-".format(get_currency,date))
        return None
    abbreviated_currency = abbreviations[get_currency.lower()]
    currency_rates_dictionary[date][abbreviated_currency] = {'rate' : rate}
    return currency_rates_dictionary
    
def save_currency_rates_dict(currency_rates_dictionary,file):

    org_filename =Path(file).stem
    league = org_filename.split('.')[0]
    json_filename = league + '_currency_rates.json'

    with io.open(json_filename,'w') as jsonf:
        try:
            jsonf.write(json.dumps(currency_rates_dictionary,indent=3))
        except Exception as e:
            logger.critical("\t\tSAVING_DICTIONARY : error -{}- while writing dictionary with rates".format(e))


def main():
    
    process_csv_files(files_to_process)
    print()

if __name__ == "__main__":    
    sys.exit(main())