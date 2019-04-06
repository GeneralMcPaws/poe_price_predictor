import json,sys,os,io
import argparse
import logging.config
import glob
import pymongo
import time
from datetime import datetime

parser = argparse.ArgumentParser(description='This program extracts data from processed stashes. ')

group1 = parser.add_mutually_exclusive_group(required=True)
group1.add_argument("-d","--dir",help="Directory where processed_stashes are stored",nargs='+')
group1.add_argument("-f","--files",help="Processed_stash file(s)",nargs='+')
parser.add_argument("-w","--whitelisting",choices=['N','n','C','c'],help="What to whitelist on : 'c' for categories 'n' for names",required=True)
parser.add_argument("-ss","--starting_stash",help="Stash_id to start processing from. Used for testing after program error",nargs=1)
parser.add_argument("-sf","--starting_file",help="Starting_file to use in -f. It should be the file that caused the program error. Used for testing",nargs=1)
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

try:
    poe_database = mongo_client[db_name]
    logger.debug("Created/Retrieved database with name : {} ".format(db_name) )
    transactions_col = poe_database["transactions"]
    stashes_snapshot_col = poe_database["stashes_snapshot"]
except Exception as e:
    logger.error("Error -{}- trying to create mongodb database and retrieve collections".format(e))
    quit()

files_to_process = []

# for option -d : directory or multiple directories as input
if args.dir:

    # for each given directory in the list check if it actually is a directory
    for d in args.dir:
        if not os.path.isdir(d):
            logger.warning('-d  {} is not a directory. Skipping ...'.format(d))
            continue

        file_pattern_search = os.path.join(d, "*")
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

        # check for every file if it is indeed a file
        f = f.strip()
        if not os.path.isfile(f):
            msg = '{0} is not a file'.format(f)
            raise argparse.ArgumentTypeError(msg)

        files_to_process.append(f)

if not files_to_process:
    logger.critical('Configuration : no files to process! Empty list.')
    quit()

if not 'NAMES_WHITELISTED' in conf.keys():
    names_whitelisted = []
else:
    names_whitelisted = conf['NAMES_WHITELISTED']
if not 'CATEGORIES_WHITELISTED' in conf.keys():
    categories_whitelisted = []
else:
    categories_whitelisted = conf['CATEGORIES_WHITELISTED']

whitelisting_option = ''

if args.whitelisting:
    if args.whitelisting[0].lower() == 'c':
        whitelisting_option = 'category'
    elif args.whitelisting[0].lower() =='n':
        whitelisting_option = 'name'
    else:
        logger.error("ERROR : Haven't specified what to whitelist based on. 'C' for categories and 'N' for names")

def populate_database():
 
    start_time = time.time()

    for file_name in files_to_process:

        stash_feed = load_poestash_file(file_name)
        if not stash_feed:
            logger.error("Could not open stash_feed {}".format(file_name))
            continue

        logger.debug("START PROCESS Filename  : " + file_name)

        result, stash_id = extract_data_from_stash_feed(stash_feed)

        if result:
            logger.debug("END PROCESS Filename : " + file_name)            
        else:
            logger.error("ERROR PROCESS stash_feed with name : " + file_name)
            logger.error("ERROR PROCESS caused from stash_id : " + stash_id)
            return 0
    total_elapsed_time = time.time() - start_time
    logger.debug("TOTAL ELAPSED TIME IN SECONDS : {}".format(total_elapsed_time))
    logger.debug("TOTAL ELAPSED TIME HOURS : {}".format(total_elapsed_time/3600))
    return 1


def extract_data_from_stash_feed(stash_feed):

    for stash in stash_feed['stashes']:
        try:
            if stashes_snapshot_col.find_one({"_id":stash['_id']}):
                logger.debug("Stash {} exists".format(stash['_id']))
                with mongo_client.start_session() as session:
                    with session.start_transaction():
                        result, id = process_existing_stash(stash,session)
            else:
                logger.debug("Stash {} does not exist. Insert all its contents".format(stash['_id']))
                with mongo_client.start_session() as session:
                    with session.start_transaction():
                        result,id = add_new_stash(stash,session)
            if not result:
                return None, id
        except Exception as e:
            logger.error("extract_data_from_stash_feed() : Error -{}- trying extract_data_from_stash_feed".format(e))
            return None, stash['_id']
    return 1,None


def add_new_stash(stash, session):
    try:
        add_stash_to_snapshot(stashes_snapshot_col, stash, session)
        #add_items_to_trx(stash, session)
        return 1,None
    except Exception as e:
        logger.error("Error -{}- while inserting new stash and items\n".format(e))
        return None, stash['_id']


def add_stash_to_snapshot(collection, stash, session):
    logger.debug("\t\tADD STASH SNAPSHOT : stash id {} \n".format(stash['_id']  ))
    try:
        collection.insert_one(stash, session=session)    
    except Exception as e:
        logger.error("\t\tADD STASH SNAPSHOT : Error -{}- stash id {} \n".format(e, stash['_id']))
        return None, stash['_id']        


def process_existing_stash(stash, session):
    
    logger.debug("\tSTART PROCESS EXISTING stash_id {} : ".format(stash['_id']))

    # result,problem_id = update_stash_datetime(stash,session)
    # if not result:
    #     return result,problem_id

    # make a copy of stash from Db
    stash_snapshot_copy = stashes_snapshot_col.find_one({"_id":stash['_id']})
    stash_snapshot_copy_dict = {}

    # Make a dictionary from the stash_snapshot array of items.
    try:
        for item in stash_snapshot_copy['items']:
            item_id = item['_id']
            stash_snapshot_copy_dict[item_id] = item
    except KeyError as err:
        logger.error("KeyError {} : Key '_id' not found in item while creating stash_snapshot_copy_dict".format(err))
        return None,stash['_id']

    # Compare the two instances of the stash, the old and the new
    # LEFT : Stash Feed 
    # RIGHT: Stash_Snapshot Db

    for item in stash['items']:
        item_id = item['_id']

        # IMPORTANT CHANGE : Added the '_id':stash['_id'] field because previously i was checking ALL THE STASHES
        item_found = stashes_snapshot_col.find_one({'_id': stash['_id'], 'items._id': item_id}, {'items.$': 1})

        # Case 1:Item still in stash
        #       item exists in old and new stash_snapshot. We do nothing
        if item_found:

            #Case 1.1 : item had a price field before and after`
            if 'price_raw' in item and 'price_raw' in item_found['items'][0]:
                # Check if the price of the item changed
                if item_found['items'][0]['price_raw'] != item['price_raw']:
                    result,problem_id = update_item_snapshot_price(stashes_snapshot_col, item, stash, session)
                    if not result:
                        return result,problem_id
                    
                    #REMOVED : update transactions only when an item is removed from stash -> thus sold
                    #result,problem_id = update_transaction_price(item,item_id, item['price_raw'], item['price_amount'], item['price_currency'], session)
                    #if not result:
                    #    return result,problem_id

            #Case 1.2 : item didn't have a price field before but now it does. Insert the new price
            elif 'price_raw' in item and 'price_raw' not in item_found['items'][0]:
                result,problem_id = update_item_snapshot_price(stashes_snapshot_col, item, stash, session)
                if not result:
                    return result,problem_id

                #REMOVED : update transactions only when an item is removed from stash -> thus sold
                #result,problem_id = update_transaction_price(item,item_id, item['price_raw'], item['price_amount'], item['price_currency'], session)
                #if not result:
                #    return result,problem_id
                
            # item is found in stash and handled
            # remove it from dictionary         
            try:
                del stash_snapshot_copy_dict[item_id]
            except Exception as e:
                logger.error("Error -{}- during deletion of item from stash_snapshot_copy_dict with id : {}".format(e, item_id))
            continue
            
        # Case 2:Item does not exist in the db snapshot -> item is new
        #       Update the transactions_col and the stash_snapshot_col with the new item 
        # NOTE: do we have to check for price? This is the condition to put it in a trx !

        else:
            result,problem_id = insert_item_to_snapshot(stashes_snapshot_col, item, stash, session)
            if not result:
                return result,problem_id
           
            #result,problem_id = insert_transaction(item,session)
            #if not result:
            #    return result,problem_id
            
    # Case 3:Item removed from stash
    #       The items remaining in stash_snapshot_copy are the ones that existed in the old snapshot
    #       but got deleted. So we have to remove them from the new copy
    #
    #        # LEFT : Stash_Snapshot Db RIGHT: Stash Feed

    if len(stash_snapshot_copy_dict.keys()) > 0:
        result = add_items_to_trx(stash_snapshot_copy_dict,stash,session)
        if not result:
            return None,stash['_id']
        result = remove_items_from_snapshot(stash_snapshot_copy_dict,session,stash['_id'])
        if not result:
            return None,stash['_id']
        
    return 1,None

def update_stash_datetime(stash,session):
    try:
        stashes_snapshot_col.update_one({'_id': stash['_id']}, 
                                            {'$set': {'date':stash['date'],
                                                      'time':stash['time'],
                                                      'date_day':stash['date_day'],
                                                      'date_month':stash['date_month'],
                                                      'date_year':stash['date_year'],
                                                      'time_minutes':stash['time_minutes'],
                                                      'time_hours':stash['time_hours']}}, upsert=True, session=session)
        return 1,None
    except Exception as e:
        logger.error("\t\tUPDATING STASH DATETIME : Error -{}- during updating stash datetime".format(e))
        return None,stash['_id']

def remove_items_from_snapshot(items_removed,session,stash_id):
    items_to_remove =[]
    for item_id in items_removed:
        items_to_remove.append(items_removed[item_id])
    try:
        stashes_snapshot_col.update_many({'_id': stash_id}, {'$pull': {'items': {'$in': items_to_remove}}}, upsert=True,session=session)
        logger.debug("\t\tREMOVE SNAPSHOT ITEMS {}".format('-'.join(items_removed.keys())))
        return 1
    except Exception as e:
        logger.error("\t\tREMOVING ITEMS :  Error -{}- during removing items from snapshot".format(e))
        return None

def add_items_to_trx(items_sold_dict,stash_last_update,session):
    for item_key in items_sold_dict:
        item = items_sold_dict[item_key]
        if whitelisting_option == 'category':
            if item['item_category'] not in categories_whitelisted:
                continue
        if whitelisting_option == 'name':
            if item['item_name'] not in names_whitelisted:
                continue
        if 'price_raw' in item:
            days_in_snapshot = calculate_days_in_snapshot(item,stash_last_update)
            price = item['price_raw']
            item['days_in_snapshot'] = days_in_snapshot
            try:
                item_found = transactions_col.find_one({"_id":item['_id']})
                if item_found:
                    if item_found['price_raw'] == price:
                        logger.debug("\t\tADD TRX : Item id already exists and it has the same price in transactions_col")
                    else:
                        result,problem_id = update_transaction_price(item,session)
                else:
                    transactions_col.insert_one(item,session=session)
                    logger.debug("\t\tADDED  TRX : Item id {} with price {} ".format(item['_id'],price))
            except Exception as e:
                logger.error("\t\tADDED  TRX :  Error -{}- during inserting transaction of item with id : {}".format(e,item['_id']))
                return None,item['stash_id']        
    return 1,None

def insert_item_to_snapshot(stashes_snapshot,item,stash,session):
    try:        
        stashes_snapshot.update_one({'_id': stash['_id']}, {'$push': {'items': item}}, upsert=True, session=session)
        logger.debug("\t\tINSERT ITEM SNAPSHOT : item id :{} ".format(item['_id']))
        return 1,None
    except Exception as e:
        logger.error("\t\tINSERT ITEM SNAPSHOT : Error -{}- during inserting item with id :{} ".format(e, item['_id']))
        return None,stash['_id']


def update_item_snapshot_price(stashes_snapshot, item, stash,session):
    logger.debug("\t\tUPDATE ITEM PRICE: Stash[{}]  Price Item {} has changed - Snapshot Updated".format(stash['_id'], item['_id']))
    try:
        stashes_snapshot.update_one({'_id': stash['_id'], 'items._id':item['_id']}, 
                                    {'$set':{'items.$.price_raw':item['price_raw'],
                                             'items.$.price_amount':item['price_amount'],
                                             'items.$.price_currency':item['price_currency'],
                                             'items.$.date':item['date'],
                                             'items.$.time':item['time'],
                                             'items.$.date_day':item['date_day'],
                                             'items.$.date_month':item['date_month'],
                                             'items.$.date_year':item['date_year'],
                                             'items.$.time_minutes':item['time_minutes'],
                                             'items.$.time_hours':item['time_hours']}}, upsert=True, session=session)
        return 1,None
    except Exception as e:
        logger.error("\t\t\t\tUPDATE ITEM PRICE : Error -{}- during updating item price of item with id : {}".format(e, item['_id']))
        return None,stash['_id']


def remove_item(stashes_snapshot, item_id, stash, session):
    try:
        stashes_snapshot.update_one({'_id': stash['_id']}, {'$pull': {'items': {'_id': item_id}}}, upsert=True, session=session)
        logger.debug("\t\tREMOVE ITEM from SNAPSHOT: Item id : {} ".format(item_id))
        return 1,None
    except Exception as e:
        logger.error("\t\tREMOVE ITEM from SNAPSHOT: Error -{}-  during removing item with id : {} ".format(e, item_id))
        return None,stash['_id']


def update_transaction_price(item,session):
    logger.debug("\t\t UPDATE TRX PRICE : Stash Price Item {} has changed to {} - Trx Updated".format(item['_id'], item['price_raw']))
    if whitelisting_option == 'category':
        if item['item_category'] not in categories_whitelisted:
            return 1,None
    if whitelisting_option == 'name':
        if item['item_name'] not in names_whitelisted:
            return 1,None
    try:        
        if transactions_col.find_one({"_id":item['_id']}):
            logger.debug("\t\tUPDATE TRX PRICE : Item_id already exists in transactions_col. Updating prices")
            transactions_col.update_one({'_id': item['_id']}, 
                                        {'$set': {'price_raw': item['price_raw'],
                                                  'price_amount':item['price_amount'],
                                                  'price_currency' : item['price_currency'],
                                                  'date':item['date'],
                                                  'time':item['time'],
                                                  'date_day':item['date_day'],
                                                  'date_month':item['date_month'],
                                                  'date_year':item['date_year'],
                                                  'time_minutes':item['time_minutes'],
                                                  'time_hours':item['time_hours'],
                                                  'days_in_snapshot':item['days_in_snapshot']}}, upsert=True, session=session)
            return 1,None
        else:
            logger.error("\t\tUPDATE TRC PRICE : Item_id does not exist to try and update it")
            return insert_transaction(item,days,session)
    except Exception as e:
        logger.error("\t\t UPDATE TRX PRICE : Error  -{}-  during updating transaction price of item with id : {} " .format(e, item['_id']))
        return None,item['_id']


def insert_transaction(item,session):
    logger.debug("\t\tINSERT NEW TRX : Item[{}] ".format(item['_id']))    
    if whitelisting_option == 'category':
        if item['item_category'] not in categories_whitelisted:
            return 1,None
    if whitelisting_option == 'name':
        if item['item_name'] not in names_whitelisted:
            return 1,None
    try:
        if transactions_col.find_one({"_id": item['_id']}):
            logger.debug("\t\tINSERT NEW TRX : Item id already exists in transactions_col")
        else:
            transactions_col.insert_one(item, session=session)
        return 1,None
    except Exception as e:
        logger.error("\t\tINSERT NEW TRX:  Error  -{}-  during inserting new transaction Item[{}] " .format(e, item['_id']))
        return None,item['_id']        

def calculate_days_in_snapshot(item,last_update_stash):
    date_format = "%Y-%m-%d"
    a = datetime.strptime(item['date'],date_format)
    b = datetime.strptime(last_update_stash['date'],date_format)
    delta = b-a
    return delta.days
    #if item['date_month'] == last_update_stash['date_month']:

def load_poestash_file(file_name):
    try:
        with io.open(file_name, 'r') as file:
            stash_feed = json.load(file)
            return stash_feed
    except Exception  as e:
        logger.error('Error -{}- : load_poestash_file {}'.format(e, file_name))
        return None

def main():

    res = populate_database()
    return res


if __name__ == "__main__":    
    sys.exit(main())
