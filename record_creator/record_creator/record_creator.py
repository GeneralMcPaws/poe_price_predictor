import json,sys,os,io
import argparse
import logging.config
import glob
import pymongo
import datetime
import pandas as pd
from Full_Feature_Recorder import Full_Feature_Recorder 
from collections import OrderedDict

parser = argparse.ArgumentParser(description='This program creates the full records from item_records')

group = parser.add_mutually_exclusive_group()

group.add_argument("-i","--item_name",help="Item name", nargs=1)
group.add_argument("-t","--item_category",help="Item category", nargs=1)
parser.add_argument("-c","--config",help="Configuration file",nargs=1)
parser.add_argument("-lo","--log_level",help="Logging level",nargs=1)
parser.add_argument("-l","--limit",help="Items find limit ",nargs=1)
parser.add_argument("-r","--rarity",help="Items find limit ",nargs=1,required=True)

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


items_limit = 0
if args.limit:
    items_limit = int(args.limit[0])

item_name = ''
item_category = ''
rarity = ''

if args.item_name:
    item_name = args.item_name[0]
elif args.item_category:
    item_category = args.item_category[0]

if args.rarity :
    rarity = args.rarity[0].lower()
    if 'rare' not in rarity or 'unique' not in rarity:
        logger.error("\t\tArgument error : Could not determine rarity of items from argument args.rarity = {}".format(rarity))

conf = conf['CONFIG']

mongo_host="mongodb://localhost:27017/"
if not 'MONGO_HOST' in conf.keys():
    logger.info("MongoDB host not defined in configuration. Connecting to default {}".format(mongo_host))
else:
    mongo_host = conf["MONGO_HOST"]

if not 'DATABASE_NAME' in conf.keys():
    logger.critical("Database name not defined. Exiting")
    quit(0)
else:
    db_name = conf["DATABASE_NAME"]

mongo_client = pymongo.MongoClient(mongo_host)

def create_csv_category_label(category_feature_record):
    csv_label = []
    for key in category_feature_record:
        csv_label.append(key)
    return csv_label

def create_category_csvs(full_feature_record_categories):
    for category in full_feature_record_categories:
        od = OrderedDict(sorted(full_feature_record_categories[category].items(), key=lambda t: t[0]))
        category_labels = create_csv_category_label(od)
        df = pd.DataFrame(data = od)
        df.to_csv('./csv/{}/{}_values.csv'.format(rarity,category),header=category_labels)

def fill_categories_record(categories,features_record,item_category):
    for key in features_record:
        try:
            categories[item_category][key].append(features_record[key])
        except Exception as e:
            logger.error("\t\tCategories fill: key {} did not exist in categories dictionary for category -{}-".format(key,item_category))
            return None
    return categories


def main():
    
    
    categories = {}

    ffr = Full_Feature_Recorder(conf=conf)
    
    start = datetime.datetime.now()

    try:
        poe_database = mongo_client[db_name]
        logger.debug("Created/Retrieved database with name : {} ".format(db_name))
        transactions_col = poe_database["transactions"]
        stashes_snapshot_col = poe_database["stashes_snapshot"]
       
        if item_name:
            pc = transactions_col.find\
                (\
                {"item_name":item_name},\
                no_cursor_timeout=True)\
                .limit(items_limit)
        elif item_category:
            pc = transactions_col.find\
                (\
                {"item_category":item_category},\
                no_cursor_timeout=True)\
                .limit(items_limit)
        else:
            pc = transactions_col.find\
                (\
                {},\
                no_cursor_timeout=True)\
                .limit(items_limit)
        count = 0
        
        for record in pc:
            count=count+1

            try:    
                item_cat = record['item_category']
                logger.debug("-->> RECORD #{}  ".format(count))

                ffrec = ffr.create_full_record(record)

                if not ffrec:
                    logger.error("ERROR : Could not create_full_record  -@- id = {} -@- cat = {} -@- item name  = {}".format(record['_id'], item_cat, record['item_name']))
                    continue
                if item_cat not in categories:
                    categories[item_cat] = {}
                    for key in ffrec:
                        categories[item_cat][key] = [ffrec[key]]
                else:
                    categories = fill_categories_record(categories,ffrec,item_cat)     
                    if not categories:
                        raise Exception("\t\tError while filling categories with values")
            except Exception as e:
                logger.error("ERROR :{}: Read Record : _id {} ".format(e, record['_id']))

            logger.info("-->> RECORD #{}  ".format(count))

    except Exception as e:
        logger.error("Error - General -{}- ".format(e))
        logger.info("Ended  with errors in : {}".format(datetime.datetime.now() - start))
        quit()

    logger.info("Ended Succesfully in : {}".format(datetime.datetime.now() - start))
    create_category_csvs(categories)

    return '0'


if __name__ == "__main__":
    sys.exit(main())

