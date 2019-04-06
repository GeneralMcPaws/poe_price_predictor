import requests,time,csv,datetime,sys
import json
import pathlib
import os
import logging.config
import argparse
import json_exceptions

parser = argparse.ArgumentParser(description='This program fetches stashes as json from the official pathOfExile api')

parser.add_argument("-s","--sid",help="Input the next_change_id from which you want to start",nargs=1)
parser.add_argument("-o","--output",help="Input the directory in which you want to save the produced files",nargs=1)
parser.add_argument("-c","--config",help="Configuration file",nargs=1)
parser.add_argument("-f","--log_level",help="Logging level to run the program",nargs=1)

args = parser.parse_args()

if args.config:
    config_file_name = args.config
else:
    config_file_name = 'fetch_stashes_config.json'

with open(config_file_name,'r') as fjson:
    conf = json.load(fjson)
if(not conf):
    #TODO: ti gurizw edw an den exw settarei logger kai den thelw na gurisw print??? ¯\_(ツ)_/¯
    print('Could not load configuration file')
    quit()

logging.config.dictConfig(conf['LOGGING'])
logger = logging.getLogger('file_console_logger')

if args.log_level:
    logging_level = getattr(logging,args.log_level[0])
    if not isinstance(logging_level,int):
        logger.error('Could not set level of logger. Argument "log_level" value was not acceptable\nlog_level = {}'.format(args.log_level[0]))
    else:
        logger.setLevel(logging_level)

conf = conf['CONFIG']

def get_stashes(starting_change_id,output_path):

    next_change_id = starting_change_id
    
    count = 0

    while(True):
        # ----------------------
        # Save last requested id
        # ----------------------
        previous_id = next_change_id

        # ----------------------
	    # construct the url to be called
	    # ----------------------
        next_url = construct_api_url(next_change_id)

        date_time = f"{datetime.datetime.now():%Y-%m-%d-%H-%M}" 
        date = f"{datetime.datetime.now():%Y-%m-%d}"

        stash_directory = handle_stash_directory(date,output_path)
        if(not stash_directory):
            logger.error('Error : get_stashes\nStash directory could not be created\n')
            continue

        logger.debug('getting stash_id = {} \t count {}'.format(next_change_id,count))
        
        stash_data = get_stash_from_url(next_url)

        if(not stash_data):
            logger.error('Error : get_stashes\nStash_data is empty\n')
            continue

        next_change_id,json_stash_data = extract_id_from_stash_data(stash_data,previous_id)
        if(not next_change_id):
            logger.error('Error : get_stashes\nCould not find field next_change_id or field wasn\'t valid\n')
            continue
        if(not json_stash_data):
            logger.error('Error : get_stashes\nJson_data empty\n')
            continue

        logger.debug('next_change_id = {}'.format(next_change_id))

        result = save_stash_data_to_file(stash_directory,json_stash_data,date_time,count)
        if(not result):
            logger.error('Error : get_stashes\nCould not save data to file\n')
        count+=1

def handle_stash_directory(date,output_path):

    #the idea is to change directories when the day changes
    #for that reason if the directory with the date we are at doesn't exist, we make it

    folder_name = 'stash_repo_'+ date
    folder_path = os.path.join(output_path,folder_name)

    try:
        pathlib.Path(folder_path).mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.error('Error : handle_stash_directory\nException raised while making the stash directory with :\nfolder_name = {}\noutput_path = {}\n'.format(folder_name,output_path))
        return None
    return folder_path

def save_stash_data_to_file(folder_name,stash_data,date_time,count):

    file_name = 'poestash_{}-{}.json'.format(date_time,count)
    directory_file_name = os.path.join(folder_name,file_name)

    try:
        with open(directory_file_name,'w') as fJSON:
            fJSON.write(json.dumps(stash_data,sort_keys=True))
        return 1
    except sys.IOError as e:
        logger.error('Error : save_stash_data_to_file\n',e)
        return 0

def get_stash_from_url(url):

    headers=conf['URL_HEADERS']
    # ----------------------
	# REQUEST URL
	# ----------------------
    logger.debug('Getting data from url : {}'.format(url))

    try:
        r=requests.get(url, headers=headers)
        r.raise_for_status()

        if(r.headers['content-type'] not in headers['content-type']):
            logger.error('Error : get_stash_from_url. Content-type error. Wanted :{} \nGot from url : {}'.format(headers['content-type'],r.headers['content-type']))
            return None

        return r.text
    except (requests.exceptions.HTTPError,
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout) as e:
        logger.error('Error : get_stash_from_url\n{}\n Retrying....\n'.format(e))
        time.sleep(conf['RETRY_WAIT_TIME'])
        return None
    except requests.exceptions.RequestException as e:
        logger.error('Error : get_stash_from_url\n',e)
        return None

def extract_id_from_stash_data(stash_data,previous_id):

    try:
        json_data = json.loads(stash_data)
        next_change_id = json_data['next_change_id']
    except json.JSONDecodeError as e:
        logger.error('Error : extract_id_from_stash_data\n',e)
        return next_change_id,None

    if(not next_change_id):
        logger.error('Error : extract_id_from_stash_data\nJson doesn\'t contain next_change_id field or nid is zero\n')
        time.sleep(conf['RETRY_WAIT_TIME'])
        return next_change_id,None
    elif(previous_id == next_change_id):
        logger.error('Error : extract_id_from_stash_data\nNo change in next_change_id. Id same as before :\n{:15} = {}\n{:15} = {}\n'
                        .format('previous_id',previous_id,'next_change_id', next_change_id))
        time.sleep(conf['RETRY_WAIT_TIME'])
        return next_change_id,None
    return next_change_id,json_data



def construct_api_url(next_change_id):

    params = {'id' : next_change_id}

    r = requests.Request('GET',conf['NEXT_STASH_BASE_URL'],conf['URL_HEADERS'],params=params).prepare()

    return r.url

def get_starting_id_from_api():

    try:
        r=requests.get(conf['NEXT_CHANGE_IDS_URL'], headers=conf['URL_HEADERS'])
        r.raise_for_status()

        if(r.headers['content-type'] not in conf['URL_HEADERS']['content-type']):
            logger.error('Error : get_id_from_url\n Considering content-type error. Wanted :{} \nGot from url : {}'.format(headers['content-type'],r.headers['content-type']))

        return r.json()['psapi']
    except(requests.exceptions.HTTPError,
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
            json_exceptions.InvalidContentType) as e:
        logger.error('Error : get_starting_id_from_api\n',e)
        time.sleep(conf['RETRY_WAIT_TIME'])
        return None
    except requests.exceptions.RequestException as e:
        logger.error('Error : get_starting_id_from_api\n',e)
        time.sleep(conf['RETRY_WAIT_TIME'])
        return None


def main():

    try:
        if args.sid:
            starting_change_id = args.sid
        else:
            starting_change_id = get_starting_id_from_api()
            if(not starting_change_id):
                raise Exception('Could not retrieve a starting_change_id')
    except Exception as e:
        logger.critical(e)
        quit(0)

    logger.debug('Started with change_id = {}'.format(starting_change_id))

    if args.output:
        output_path = os.path.abspath(args.output[0])
    else:        
        output_path = os.path.abspath(conf['OUTPUT_PATH'])

        
    logger.debug('Writing in directory : {}'.format(output_path))

    get_stashes(starting_change_id,output_path)

if __name__ == "__main__":
    sys.exit(main())
