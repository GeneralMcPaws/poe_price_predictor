import re,json,io,sys,os
import argparse
import logging.config
import pathlib
import glob

parser = argparse.ArgumentParser(description='Program produces the template dictionaries of features for items')

parser.add_argument("-d","--dir",help="Directory where Features are stored",nargs='+',required = True)
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
    logging.basicConfig(level=logging.CRITICAL,format='%(levelname)s:%(message)s')
    logging.getLogger('file_console_logger').critical('Critical error in initializing the configuration of the program\nExiting!')
    quit(0)

logging.config.dictConfig(conf['LOGGING'])
logger = logging.getLogger('file_logger')

if args.log_level:
    logging_level = getattr(logging,args.log_level[0])
    if not isinstance(logging_level,int):
        logger.error('Could not set level of logger. Argument "log_level" value was not acceptable\nlog_level = {}'.format(args.log_level[0]))
    else:
        logger.setLevel(logging_level)

conf = conf['CONFIG']

def get_league_folders_from_argument():

    leagues_to_process = []

    #for option -d : directory or multiple directories as input
    if args.dir:
        #for each given directory in the list check if it actually is a directory
        for d in args.dir:
            if not os.path.isdir(d):
                logger.warning('Configuration : {} is not a directory'.format(d))
                continue
            #and if there are any league folders underneath it
            if(not d.endswith('\\')):
                d = d+'\\'
            league_folders = glob.glob(d+'*\\')
            if not league_folders:
                logger.warning('Configuration : {} directory has no league folders in it'.format(d))
                continue
            for league_path in league_folders:
                if pathlib.PurePath(league_path).name in conf["LEAGUES"]:
                    leagues_to_process.append(league_path)

    if not leagues_to_process:
        logger.critical('Configuration : no league_directories to process! Empty list.')
        quit()

    return leagues_to_process

def process_league_features_to_template(league_folder_path):
    rare_mods_path = league_folder_path+'rare_explicit_mods\\Json\\' if pathlib.Path(league_folder_path+'rare_explicit_mods\\Json\\').is_dir() else None
    unique_mods_path = league_folder_path+'unique_explicit_mods\\Json\\' if pathlib.Path(league_folder_path+'rare_explicit_mods\\Json\\').is_dir() else None
    corrupted_mods_path = league_folder_path+'corrupted_mods\\Json\\' if pathlib.Path(league_folder_path+'rare_explicit_mods\\Json\\').is_dir() else None
    implicit_mods_path = league_folder_path+'implicit_mods\\Json\\' if pathlib.Path(league_folder_path+'rare_explicit_mods\\Json\\').is_dir() else None
    enchantment_mods_path = league_folder_path+'enchantment_mods\\Json\\' if pathlib.Path(league_folder_path+'rare_explicit_mods\\Json\\').is_dir() else None
    attribute_mods_path = league_folder_path+'attribute_mods\\Json\\' if pathlib.Path(league_folder_path+'rare_explicit_mods\\Json\\').is_dir() else None
    common_mods_file_path = league_folder_path+'common_mods.json' if pathlib.Path(league_folder_path+'common_mods.json').exists() else None

    if not rare_mods_path:
        logger.error("ERROR getting league mods : rare_explicit_mods\\Json folder does not exist")
        return None
    if not unique_mods_path:
        logger.error("ERROR getting league mods : unique_mods_path\\Json folder does not exist")
        return None
    if not corrupted_mods_path:
        logger.error("ERROR getting league mods : corrupted_mods_path\\Json folder does not exist")
        return None
    if not implicit_mods_path:
        logger.error("ERROR getting league mods : implicit_mods_path\\Json folder does not exist")
        return None
    if not enchantment_mods_path:
        logger.error("ERROR getting league mods : enchantment_mods_path\\Json folder does not exist")
        return None
    if not attribute_mods_path:
        logger.error("ERROR getting league mods : attribute_mods_path\\Json folder does not exist")
        return None
    if not common_mods_file_path:
        logger.error("ERROR getting common_mods : {}\\common_mods.json does not exist".format(league_folder_path))
        return None

    rare_features_template = create_features_template(rare_mods_path,corrupted_mods_path,implicit_mods_path,enchantment_mods_path,attribute_mods_path,common_mods_file_path,league_folder_path,'rare')
    unique_features_template = create_features_template(unique_mods_path,corrupted_mods_path,implicit_mods_path,enchantment_mods_path,attribute_mods_path,common_mods_file_path,league_folder_path,'unique')
    return 1
def create_features_template(primary_mods_path,corrupted_mods_path,implicit_mods_path,enchantment_mods_path,attribute_mods_path,common_mods_file_path,league_folder_path,rarity):

    primary_directory_files = glob.glob(primary_mods_path+'*')
    if not primary_directory_files:
        logger.error("Primary directory {} has no mod files in it".format(primary_mods_path))
        return None
    for primary_file_path in primary_directory_files:
        concatenated_features = {}
        if not pathlib.PurePath(primary_file_path).match('*.json'):
            logger.error("ERROR : incorrect extension for file-{}-".format(pathlib.PurePath(primary_file_path).name))
            continue
        primary_file_name = pathlib.PurePath(primary_file_path).name
        category = primary_file_name.split('_')[0]
        logger.debug("Processing primary_mod_file {}".format(primary_file_name))
        implicit_file_path = implicit_mods_path + category + '_implicit_mods.json'
        enchantment_file_path = enchantment_mods_path + category + '_enchantment_mods.json'
        corrupted_file_path = corrupted_mods_path + category + '_corrupted_mods.json'
        attribute_file_path = attribute_mods_path + category + '_attribute_mods.json'
        with io.open(primary_file_path,'r') as prim_json:
            prim_features_dic = json.load(prim_json)
            for k in prim_features_dic:
               if k not in concatenated_features:
                   concatenated_features['ex_'+k] = 0
        if not pathlib.Path(implicit_file_path).exists():
            logger.error("ERROR : implicit file {} does not exist".format(pathlib.PurePath(implicit_file_path).name))
        else:
            with io.open(implicit_file_path,'r') as im_json:
                im_features_dic = json.load(im_json)
                #concatenate two dictionaries
                for k in im_features_dic:
                    if k not in concatenated_features:
                        concatenated_features['im_'+k] = 0
        if not pathlib.Path(enchantment_file_path).exists():
            logger.error("ERROR : enchantment file {} does not exist".format(pathlib.PurePath(enchantment_file_path).name))
        else:
            with io.open(enchantment_file_path,'r') as en_json:
                en_features_dic = json.load(en_json)
                #concatenate two dictionaries
                if concatenated_features:
                    for k in en_features_dic:
                        if k not in concatenated_features:
                            concatenated_features['en_'+k] = 0
        if not pathlib.Path(corrupted_file_path).exists():
            logger.error("ERROR : corrupted file {} does not exist".format(pathlib.PurePath(corrupted_file_path).name))
        else:
            with io.open(corrupted_file_path,'r') as co_json:
                co_features_dic = json.load(co_json)
                #concatenate two dictionaries
                if concatenated_features:
                    for k in co_features_dic:
                        if k not in concatenated_features:
                            concatenated_features['co_'+k] = 0
        if not pathlib.Path(attribute_file_path).exists():
            logger.error("ERROR : attribute file {} does not exist".format(pathlib.PurePath(attribute_file_path).name))
        else:
            with io.open(attribute_file_path,'r') as at_json:
                at_features_dic = json.load(at_json)
                #concatenate two dictionaries
                if concatenated_features:
                    for k in at_features_dic:
                        if k not in concatenated_features:
                            concatenated_features[k] = 0
        if not pathlib.Path(common_mods_file_path).exists():
            logger.error("ERROR : common mods file {} does not exist".format(pathlib.PurePath(common_mods_file_path).name))
        else:
            with io.open(common_mods_file_path,'r') as at_json:
                common_features_dic = json.load(at_json)
                #concatenate two dictionaries
                if concatenated_features:
                    for k in common_features_dic:
                        if k not in concatenated_features:
                            concatenated_features[k] = 0
        save_concatenated_features(concatenated_features,league_folder_path,category,rarity)

def save_concatenated_features(concatenated_features,league_folder_path,category,rarity):
    
    pathlib.Path(league_folder_path+rarity+'_concatenated_mods').mkdir(exist_ok=True)
    with io.open(league_folder_path+rarity+'_concatenated_mods\\'+category+'_concatenated_mods.json','w',encoding='ASCII') as fjson:
        fjson.write(json.dumps(concatenated_features,indent=2))

    

def main():

    leagues_to_process = get_league_folders_from_argument()    
    for league_folder_path in leagues_to_process:
        league_features_ml_template = process_league_features_to_template(league_folder_path)
        if not league_features_ml_template:
            logger.error("ERROR : Could not create league features template for ml")
            return 'ERROR'

    return 'Finished'


if __name__ == "__main__":
    sys.exit(main())