##ARGUMENTS
# 1. document with lines you want to process
# 2. ??database you want to append it into??


import re,json,io,sys,os
from constants import Constant
import argparse
import logging.config
import Lazy_Mods
import pathlib
import glob

parser = argparse.ArgumentParser(description='This program reformats stash data from json files')

group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("-d","--dir",help="Input the directory/ies in which all the data you wish to process is stored",nargs='+')
group.add_argument("-f","--files",help="File(s) to process",nargs='+')
parser.add_argument("-c","--config",help="Configuration file",nargs=1)
parser.add_argument("-l","--league",help="Which leagues to process",nargs='+',required=True)
parser.add_argument("-lo","--log_level",help="Logging level",nargs=1)
parser.add_argument("-o","--output",help="Directory to save the produced files in",nargs=1)
parser.add_argument("-r","--rarity",help="Rarity of items to check",nargs=1)

args = parser.parse_args()

if args.config:
    config_file_name = args.config
else:
    config_file_name = 'feed_preprocessor_config.json'

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

if args.output:
    output_path = os.path.abspath(args.output[0])
else:        
    output_path = os.path.abspath(conf['OUTPUT_PATH'])

pathlib.Path(output_path).mkdir(parents=True, exist_ok=True) 

mods = Lazy_Mods.Mods(conf)

files_to_process = []

#for option -d : directory or multiple directories as input
if args.dir:
    #for each given directory in the list check if it actually is a directory
    for d in args.dir:
        if not os.path.isdir(d):
            logger.warning('Configuration : {} is not a directory'.format(d))
            continue
        #and if there are any files underneath it
        if(not d.endswith('\\')):
            d = d+'\\'
        directory_files = glob.glob(d+'*')
        if not directory_files:
            logger.warning('Configuration : {} directory has no files in it'.format(d))
            continue
        for f in directory_files:
            #check if f is a file because glob.glob also returns directories
            if(not os.path.isfile(f)):
                logger.warning('Configuration : {} is not a file'.format(f))
                continue
            files_to_process.append(f)
          
#for option -f : input give is a file or multiple files
if args.files:
    for f in args.files:
        #check for every file if it is indeed a file
        if not os.path.isfile(f):
            msg = '{0} is not a file'.format(f)
            raise argparse.ArgumentTypeError(msg)
        files_to_process.append(f)

if not files_to_process:
    logger.critical('Configuration : no files to process! Empty list.')
    quit()

rarity_to_check = 3

if args.rarity:
    if args.rarity[0].upper() == 'RARE':
        logger.debug("Checking only rare items")
        rarity_to_check = 2

if args.league:
    currency_rates_path = conf["CURRENCY_RATES"].format(args.league[0])
    try:
        if pathlib.Path(currency_rates_path).exists():
            with io.open(currency_rates_path,'r') as f:
                currency_rates_dict = json.load(f)
    except Exception as e:
        logger.error("\t\tGET_CURRENCY_RATES : Could not open -{}- currency rates path".format(currency_rates_path))
        quit()
else:
    logger.error("\t\tERROR : No league in arguments specified. Can't get currency rates")
    quit()

def process_files(file_name_list):
    for file_name in file_name_list:
        processed_file = process_file(file_name)
        if not processed_file:
            logger.critical('Error : process_files. Could not process {} file'.format(file_name))
            continue
        result = save_processed_file(processed_file,file_name)
        if not result:
            logger.critical('Error : process_files. Could not save processed file {}'.format(file))
            continue

def process_file(file_name):
    count = 0
    #--------------------------
	# get date and time
	#--------------------------

    date_time_count = Constant.DATE_TIME_COUNT_REGEX.findall(file_name)
    try:
        date ='{}-{}-{}'.format(date_time_count[0][0],date_time_count[0][1],date_time_count[0][2])
        date_year = date_time_count[0][0]
        date_month = date_time_count[0][1]
        date_day = date_time_count[0][2]
        time ='{}-{}'.format(date_time_count[0][3],date_time_count[0][4])
        time_hours = date_time_count[0][3]
        time_minutes = date_time_count[0][4]
        stash_feed_count = date_time_count[0][5]
    except Exception as e:
        logger.critical('Error : process_file\n{} file_name does not meet the requirements. Cannot find date and/or time'.format(file_name))
        return None
    
    if date not in currency_rates_dict:
        logger.error("ERROR process_file : do not have the currency_rates for date {}".format(date))
        return None

    try:
        with io.open(file_name) as f:
            stashes_data = json.load(f)
    except json.JSONDecodeError as e:
        logger.critical('Error : process_file\nCould not load {} to dictionary'.format(file_name))
        return None

    if not stashes_data['next_change_id']:
        logger.critical('Error : process_files\nFile "{}" does not have a next_change_id field'.format(file_name))
        return None

    processed_stash_data = {"next_change_id":stashes_data['next_change_id'],'stashes':[]}

    for stash in stashes_data['stashes']:
        
	    #--------------------------
	    # NON VALID STASH
	    #--------------------------

        #TODO: Write a better , more descriptive logger
        if (not stash['public'] or stash['accountName']==None):
            logger.warning('Warning : process_file\nStash is not public or account name is null')
            continue
        try:
            new_stash_data = {'_id':stash['id'],
					        'account_name':stash['accountName'],
                            'last_character_name':stash['lastCharacterName'],
					        'stash_type':stash['stashType'][0],
                            'stash_feed':os.path.basename(file_name),
                            'date':date,
                            'date_day':date_day,
                            'date_month':date_month,
                            'date_year':date_year,
                            'time_minutes':time_minutes,
                            'time_hours':time_hours,
                            'time':time,
                            'stash_feed_count':stash_feed_count,
					        'items':[]}
        except IndexError as e:
            logger.critical('Index out of range for stash["stashType"] = {}\n'.format(stash['stashType']),e)
            new_stash_data = {'_id':stash['id'],
					        'account_name':stash['accountName'],
                            'last_character_name':stash['lastCharacterName'],
					        'stash_type':stash['stashType'],
                            'stash_feed':os.path.basename(file_name),
                            'date':date,
                            'date_day':date_day,
                            'date_month':date_month,
                            'date_year':date_year,
                            'time_minutes':time_minutes,
                            'time_hours':time_hours,
                            'time':time,
                            'stash_feed_count':stash_feed_count,
					        'items':[]}

        for item in stash['items']:
            newItemData = {}

            #--------------------------
	        # CATEGORIES/RARITIES EXCLUSION
	        #--------------------------
            if (list(item['category'].keys())[0] in conf['EXCLUDE_MODS_CATEGORY'] or item['frameType'] != rarity_to_check):
                continue

            #--------------------------
	        # DAILY EXALT CONVERION RATE
	        #--------------------------
            newItemData['ex_conv_rate'] = currency_rates_dict[date]['exa']['rate']
            
                
            #--------------------------
	        # PRICE
	        #--------------------------
	        #the [0] below is needed because this is a tuple with the second number being how many changes were made
            if ('~price' in stash['stash'] or '~b/o' in stash['stash']):
                newItemData['price_raw'] = Constant.PRICE_REGEX.subn(r'\2_\3',stash['stash'])[0]
                newItemData['price_amount'] = Constant.PRICE_REGEX.subn(r'\2',stash['stash'])[0]		
                newItemData['price_currency'] = Constant.PRICE_REGEX.subn(r'\3',stash['stash'])[0]
                if 'chaos' not in newItemData['price_currency'] and newItemData['price_currency'] in currency_rates_dict[date]:
                    try:
                        rate = float(currency_rates_dict[date][newItemData['price_currency']]['rate'])
                        price_amount = rate* float(newItemData['price_amount'])
                        newItemData['price_amount'] = price_amount
                        newItemData['price_currency'] = 'chaos'
                    except Exception as e:
                        logger.error("\t\tCURRENCY ERROR -{}- : could not get currency '{}'".format(e,stash['stash']))

            #--------------------------
			# ITEM NAME
			#--------------------------
            if(not Constant.ITEM_NAME_REGEX.search(item['name']) and item['name']==""):
                newItemData['item_name'] = item['typeLine']
            else:
                newItemData['item_name'] = Constant.ITEM_NAME_REGEX.subn(r'\1',item['name'])[0] + ' ' +item['typeLine']

            #--------------------------
			# LEAGUE
			#--------------------------
            if args.league:
                if item['league'] in args.league:
                    newItemData['league'] = item['league']
                else:
                    logger.warning('{} item is in league {} but we care about {}'.format(newItemData['item_name'],item['league'],args.league))
                    continue
            else:
                if item['league'] in conf['LEAGUES']:
                    newItemData['league'] = item['league']
                else:
                    logger.warning('{} item is in league {} but we care about {}'.format(newItemData['item_name'],item['league'],conf['LEAGUES']))
                    continue

			#--------------------------
			# ILVL, ITEMCATEGORY
			#--------------------------
            newItemData['item_level'] = item['ilvl']
            if(list(item['category'].keys())[0] in 'leaguestones'):
                 continue
            elif(list(item['category'].keys())[0] in conf['MONO_ITEMS']):
                newItemData['item_category'] = list(item['category'].keys())[0]
            else:
                newItemData['item_category'] = list(item['category'].values())[0][0]
                if(newItemData['item_category'] == 'sceptre'):
                    newItemData['item_category'] = 'onemace'
                #if(Constant.WEAPONS_REGEX.search(list(item['category'].values())[0][0])):
                #    newItemData['item_category'] = list(item['category'].values())[0][0]
                #else:
                #    newItemData['item_category'] = list(item['category'].values())[0][0]

            if any (abyss_jewel_name in item['typeLine'].lower() for abyss_jewel_name in ['murderous','hypnotic','ghastly','searching']) :
                newItemData['item_category'] = 'abyssal'
            if newItemData['item_category'] == 'rod':
            	continue
            #--------------------------
			# DATE, TIME, STASH_ID
			#-------------------------- 
            newItemData['date'] = date
            newItemData['time'] = time
            newItemData['stash_feed_count'] = stash_feed_count
            newItemData['stash_feed'] = os.path.basename(file_name)
            newItemData['stash_id'] = stash['id']
            newItemData['date'] = date
            newItemData['date_day'] = date_day
            newItemData['date_month'] = date_month
            newItemData['date_year'] = date_year
            newItemData['time_minutes'] = time_minutes
            newItemData['time_hours'] = time_hours

			#--------------------------
			# RARITY
			#--------------------------
			# 0 = normal
			# 1 = magic
			# 2	= rare
			# 3	= unique
			# 4	= gem
			# 5	= currency
			# 6	= divination card
			# 7	= quest item
			# 8	= prophecy
			# 9 = relic

            newItemData['rarity'] = item['frameType']

			#--------------------------
			# ID
			#--------------------------
            newItemData['_id'] = item['id']
            
			#--------------------------
			# SOCKETS
			#--------------------------
			#socket[group] is 1 if socket is linked and 0 if it is not
			#socket[sColour] is G, W, R, B, A. Stands for: green, white, red, blue, abyss

            newItemData['sockets_number'] = 0
            newItemData['linked_sockets'] = 0
            newItemData['socket_colors'] = ""
            if('sockets' in item):
                linked_sockets_dic = {}
                for socket in item['sockets']:
                    if socket['group'] not in linked_sockets_dic:
                        linked_sockets_dic[socket['group']] = 1
                    else:
                        linked_sockets_dic[socket['group']] = linked_sockets_dic[socket['group']] +1
                    newItemData['sockets_number'] +=1
                    #newItemData['linked_sockets'] += socket['group']
                    newItemData['socket_colors'] += socket['sColour']+'-'
                max = -1
                for group in linked_sockets_dic:
                    if linked_sockets_dic[group] > max:
                        max = linked_sockets_dic[group]
                newItemData['linked_sockets'] += max
                newItemData['socket_colors'] = newItemData['socket_colors'][:-1]
                
			#--------------------------
			# INDIVIDUAL PRICE
			#--------------------------
            if('note' in item):
                if ('~price' in item['note'] or '~b/o' in item['note']):
                    newItemData['price_raw'] = Constant.PRICE_REGEX.subn(r'\2_\3',item['note'])[0]
                    newItemData['price_amount'] = Constant.PRICE_REGEX.subn(r'\2',item['note'])[0]        
                    newItemData['price_currency'] = Constant.PRICE_REGEX.subn(r'\3',item['note'])[0]
                    if 'chaos' not in newItemData['price_currency'] and newItemData['price_currency'] in currency_rates_dict[date]:
                        try:
                            rate = float(currency_rates_dict[date][newItemData['price_currency']]['rate'])
                            price_amount = rate* float(newItemData['price_amount'])
                            newItemData['price_amount'] = price_amount
                            newItemData['price_currency'] = 'chaos'
                        except Exception as e:
                            logger.error("\t\tCURRENCY ERROR -{}- : could not get currency '{}'".format(e,item['note']))

			#--------------------------
			# INFLUENCE
			#--------------------------
            if('elder' in item):
                newItemData['influence'] = 2
            elif('shaper' in item):
                newItemData['influence'] = 1
            else:
                newItemData['influence'] = 0

			#unidentified items do not have properties or mods
            if(not item['identified']):
                continue
			#--------------------------
			# CORRUPTION
			#--------------------------
            if('corrupted' in item):
                newItemData['corrupted'] = 1
			#--------------------------
			# PROPERTIES
			#--------------------------
            if('properties' in item):
                for property in item['properties']:
                    if(property['name'] in conf['FLAT_VALUES_CATEGORY']):
                        newItemData[property['name']] = property['values'][0][0]
                    elif(property['name'] in conf['PERCENTAGE_CATEGORY']):
                        newItemData[property['name']] = Constant.PERCENTAGE_REGEX.subn(r'\1',property['values'][0][0])[0]
                    elif(property['name'] in conf['DAMAGE_CATEGORY']):
                        damageRange = Constant.DAMAGE_REGEX.findall(property['values'][0][0])
                        damageAverage = (int(damageRange[0]) + int(damageRange[1])) /2
                        newItemData[property['name']] = damageAverage
            #newItemData["physical_damage"] = newItemData.pop("Physical Damage",0)
            #newItemData["elemental_damage"] = newItemData.pop("Elemental Damage",0)
            #newItemData["critical_strike_chance"] = newItemData.pop("Critical Strike Chance",0)
            #newItemData["attacks_per_second"] = newItemData.pop("Attacks per Second",0)
            #newItemData["armour"] = newItemData.pop("Armour",0)
            #newItemData["energy_shield"] = newItemData.pop("Energy Shield",0)
            #newItemData["evasion_rating"] = newItemData.pop("Evasion Rating",0)
            #newItemData["chance_to_block"] = newItemData.pop("Chance to Block",0)

			#TODO : treat enchantment mods the same way we treat base mods??
            if('enchantMods' in item):
                enchant_mod = item['enchantMods'][0].strip(' \t\n\r').lower()
                if '\n' in enchant_mod:
                        enchant_mod = enchant_mod.replace('\n',' ')
                category_mods = mods.get_mod('enchantment',newItemData['item_category'],league=newItemData['league'])
                if not category_mods:
                    logger.critical('''\t\tBRINGING CATEGORY_MODS : ERROR trying to bring category mods.
                    LEAGUE:{}
                    ITEM_CATEGORY{}
                    '''.format(newItemData['league'],newItemData['item_category']+'_enchantment_mods'))
                general_mod = generalize_mod(enchant_mod,category_mods,newItemData['item_category'],'enchantment_'+newItemData['item_category'])
                if not general_mod:
                    logger.critical('''\nError: process_file - in enchantment mods
                                    in file_name = {}
                                    item_name = {}
                                    item_category = {}
                                    mod = {}'''.format(file_name,newItemData['item_name'],'enchantment_'+newItemData['item_category'],enchant_mod))
                newItemData['enchantment_mod'] = general_mod
             
            hardcoded_name = check_hardcoded_name(newItemData['item_name'])
            if(hardcoded_name == 1):
                continue
            elif(hardcoded_name ==2):
                newItemData['item_name'] = 'Mjolner Gavel'

            if(('explicitMods' in item) and (newItemData['item_category'] not in conf['EXCLUDE_MODS_CATEGORY'])):
                explicit_mods = item['explicitMods']
                if newItemData['rarity'] == 3 : category_mods = mods.get_mod('unique_explicit',newItemData['item_category'],league=newItemData['league'])
                else : category_mods = mods.get_mod('rare_explicit',newItemData['item_category'],league=newItemData['league'])
                if not category_mods:
                    logger.critical('''\t\tBRINGING CATEGORY_MODS : ERROR trying to bring category mods.
                    LEAGUE:{}
                    ITEM_CATEGORY{}
                    '''.format(newItemData['league'],newItemData['item_category']+'_explicit_mods'))
                newItemData['explicit_mods'] = []
                for mod in explicit_mods:
                    mod = mod.strip(' \t\n\r').lower()
                    if '\n' in mod:
                        mod = mod.replace('\n',' ')
                    general_mod = generalize_mod(mod,category_mods,newItemData['item_category'],'explicit_'+newItemData['item_category'])
                    if not general_mod:
                        logger.critical('''\nError: process_file - in explicit mods
                                        in file_name = {}
                                        item_name = {}
                                        item_category = {}
                                        mod = {}'''.format(file_name,newItemData['item_name'],'explicit_'+newItemData['item_category'],mod))
                    newItemData['explicit_mods'].append(general_mod)

            if('implicitMods' in item):
                if('corrupted' in item):
                    corrupted_mods = item['implicitMods']
                    category_mods = mods.get_mod('corrupted',newItemData['item_category'],league=newItemData['league'])
                    if not category_mods:
                        logger.critical('''\t\tBRINGING CATEGORY_MODS : ERROR trying to bring category mods.
                        LEAGUE:{}
                        ITEM_CATEGORY{}
                        '''.format(newItemData['league'],newItemData['item_category']+'_corrupted_mods'))
                    newItemData['corrupted_mods'] = []
                    for mod in corrupted_mods:
                        mod = mod.strip(' \t\n\r').lower()
                        if '\n' in mod:
                            mod = mod.replace('\n',' ')
                        general_mod = generalize_mod(mod,category_mods,newItemData['item_category'],'corrupted_'+newItemData['item_category'])
                        if not general_mod:
                            logger.critical('''\nError: process_file - in corrupted mods
                                            in file_name = {}
                                            item_name = {}
                                            item_category = {}
                                            mod = {}'''.format(file_name,newItemData['item_name'],'corrupted_'+newItemData['item_category'],mod))
                        newItemData['corrupted_mods'].append(general_mod)
                else:
                    implicit_mods = item['implicitMods']
                    category_mods = mods.get_mod('implicit',newItemData['item_category'],league=newItemData['league'])
                    if not category_mods:
                        logger.critical('''\t\tBRINGING CATEGORY_MODS : ERROR trying to bring category mods.
                        LEAGUE:{}
                        ITEM_CATEGORY{}
                        '''.format(newItemData['league'],newItemData['item_category']+'_implicit_mods'))
                    newItemData['implicit_mods'] = []
                    for mod in implicit_mods:
                        mod = mod.strip(' \t\n\r').lower()
                        if '\n' in mod:
                            mod = mod.replace('\n',' ')
                        general_mod = generalize_mod(mod,category_mods,newItemData['item_category'],'implicit_'+newItemData['item_category'])
                        if not general_mod:
                            logger.critical('''\nError: process_file - in implicit mods
                                            in file_name = {}
                                            item_name = {}
                                            item_category = {}
                                            mod = {}'''.format(file_name,newItemData['item_name'],'implicit_'+newItemData['item_category'],mod))
                        newItemData['implicit_mods'].append(general_mod)

            count+=1
            new_stash_data['items'].append(newItemData)
        
        processed_stash_data['stashes'].append(new_stash_data)
    return processed_stash_data

def save_processed_file(processed_file,file_name):

    new_file_name ='processed_'+os.path.basename(file_name)
    new_file_path = os.path.join(output_path,new_file_name)
    try:
        with io.open(new_file_path,'w',encoding='ASCII') as f:
            f.write(json.dumps(processed_file))
    except Exception as e:
        logger.critical(e,
                     '\nError: save_processed_file',
                     '\nCould not save processed_file : {}\nin output_path = {}'.format(file_name,new_file_path))
        return 0
    return 1

def generalize_mod(mod,category_mods,item_category,mod_category_name):

    param_value = None

    matches = Constant.LINE_REGEX.findall(mod)
    if not matches:
        general_mod = mod
        #format = <category>_<value>_<feature/mod>
        return '{}_{}_{}'.format(item_category,param_value,general_mod)
    number_groups = [matches[0][1],matches[0][3],matches[0][5]]
    #in case the mod has no matches or 3 number matches then we leave the mod as is
    #the general mod is the original one and that is what we need
    if (number_groups[2] and number_groups[1] and number_groups[0]):
        general_mod = mod
    #case of having 2 numbers or 1 number as matches. We check to see which of the two is a "ranged" case
    #and for this match we check to see if it has a "to". If it does we have to convert it to an average value
    else:        
        if(number_groups[1] and number_groups[0]):
            general_mod = Constant.LINE_REGEX.subn(r'\1#\3#\5', mod)[0]
            try:
                for i in range(len(category_mods[general_mod]['params'])):
                    if category_mods[general_mod]['params'][i]['type'] == 'R':
                        if 'to' in number_groups[i]:
                            damageRange = Constant.DAMAGE_REGEX.findall(number_groups[i])
                            damageAverage = (int(damageRange[0]) + int(damageRange[1])) /2
                            param_value = damageAverage
                        else:
                            param_value = number_groups[i]
            except (KeyError,OverflowError) as e:
                save_missing_feature(general_mod,mod_category_name)
                logger.critical('''Error : generalize_mod
                             mod = {}
                             general_mod = {}
                             number_group[0] = {}
                             number_group[1] = {}'''.format(mod,general_mod,number_groups[0],number_groups[1]))
                return None
        else:
            general_mod = Constant.LINE_REGEX.subn(r'''\1#\3''', mod)[0]
            try:
                if category_mods[general_mod]['params'][0]['type'] == 'R':
                    if 'to' in number_groups[0] or '-' in number_groups[0]:
                        damageRange = Constant.DAMAGE_REGEX.findall(number_groups[0])
                        if len(damageRange) == 2:
                            damageAverage = (int(damageRange[0]) + int(damageRange[1])) /2
                        else:
                            damageAverage = int(damageRange[0])
                        param_value = damageAverage
                    else:
                        param_value = number_groups[0]
            except KeyError as e:
                save_missing_feature(general_mod,mod_category_name)
                logger.critical('''Error : generalize_mod
                             mod = {}
                             general_mod = {}
                             number_group[0] = {}'''.format(mod,general_mod,number_groups[0]))
                return None
    #format = <category>_<value>_<feature/mod>
    return '{}_{}_{}'.format(item_category,param_value,general_mod)

def save_missing_feature(general_mod,mod_category):
    if rarity_to_check ==2: 
        filename = './missing_features/'+'rare_'+mod_category+'.json'
    else:
        filename = './missing_features/'+'unique_'+mod_category+'.json'
    try:
        if pathlib.Path(filename).exists():
            with io.open(filename,'r') as f:
                dict = json.load(f)
            if general_mod in dict:
                return

            dict[general_mod] = ''
            with io.open(filename,'w') as file:
                file.write(json.dumps(dict,indent=3))
        else:
            with io.open(filename,'w') as file:
                dict = {}
                dict[general_mod] = ''
                file.write(json.dumps(dict,indent=3))
    except Exception as e:
        logger.error("\t\tError -{}- trying to write missing feature".format(e))

def check_hardcoded_name(item_name):
    if 'The Hungry Loop Unset Ring' in item_name:
        return 1
    elif 'Mjölner Gavel' in item_name:
        return 2

def main():

    process_files(files_to_process)

    return 'Finished'

if __name__ == "__main__":
    sys.exit(main())
