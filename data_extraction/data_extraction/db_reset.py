#pylint:   disable-all

import json,sys,os,io
import argparse
import logging.config
import glob
import pymongo
 
parser = argparse.ArgumentParser(description='Mongdb delete all docs  from collections ')

group = parser.add_mutually_exclusive_group(required=True)

parser.add_argument("-c","--config",help="Configuration file",nargs=1)
group.add_argument("-n","--collections",help="Collections to delete",nargs='+')
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

    collections_to_delete = []
    if args.collections and args.collections[0] == 'all':
        collection = poe_database.collection_names(include_system_collections=False)
        for collect in collection:
            collections_to_delete.append(collect)
    else :
        collections_to_delete = args.collections

    for col in collections_to_delete:
        print (col)

    stashes_snapshot_col.delete_many({})
    transactions_col.delete_many({})

except Exception as e:
    logger.error("Error -{}- deleting  collections".format(e))
    quit()


 