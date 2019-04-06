import requests,time,csv,datetime,sys,json,os
import argparse
import json_exceptions
import logging.config

parser = argparse.ArgumentParser(description='This program fetches the stash change_ids from a source')

parser.add_argument("-d","--dir",help="Input the directory in which you want to save the produced files",nargs=1)
parser.add_argument("-c","--config",help="Configuration file",nargs=1)
parser.add_argument("-f","--log_level",help="Logging level to run the program",nargs=1)

args = parser.parse_args()

if args.config:
    config_file_name = args.config
else:
    config_file_name = 'fetch_change_ids_config.json'

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

def get_id_from_url(url,headers):

    # ----------------------
	# REQUEST URL
	# ----------------------
    try:
        r=requests.get(url, headers=headers)
        r.raise_for_status()

        if(r.headers['content-type'] not in headers['content-type']):
            logger.error('Error : get_id_from_url\n Considering content-type error. Wanted :{} \nGot from url : {}'.format(headers['content-type'],r.headers['content-type']))
            return None

        return r.text
    except (requests.exceptions.HTTPError,
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
            json_exceptions.InvalidContentType) as e:
        logger.error('Error : get_id_from_url\n',e)
        time.sleep(conf['RETRY_WAIT_TIME'])
        return None
    except requests.exceptions.RequestException as e:
        logger.error('Error : get_id_from_url\n',e)
        time.sleep(conf['RETRY_WAIT_TIME'])
        return None

# ----------------------
# EXTRACT ID
# ----------------------
def extract_id_from_response(response_text,previous_id):

    try:
        json_data = json.loads(response_text)
        next_change_id = json_data['psapi']
    except json.JSONDecodeError as e:
        logger.error('Error : extract_id_from_response\n',e)
        time.sleep(conf['RETRY_WAIT_TIME'])
        return None

    if(not next_change_id):
        logger.error('Error : extract_id_from_response\nJson doesn\'t contain next_change_id field or nid is zero')
        time.sleep(conf['RETRY_WAIT_TIME'])
        return None
    # no change in id
    elif(previous_id == next_change_id):
        logger.error('Error : extract_id_from_response\nNo change in next_change_id. Id same as before')
        time.sleep(conf['RETRY_WAIT_TIME'])
        return None
    return next_change_id
    

# ----------------------
# SAVE ID IN FILE
# ----------------------
def save_change_id_to_file(output_file_name, next_change_id,count):

    date_time = f"{datetime.datetime.now():%Y-%m-%d-%H-%M}"   
    formatted_line = ('{}::{}__{}\n'.format(next_change_id,date_time,count))

    try:               
        with open(output_file_name,'a') as file:
            file.write(formatted_line)
    except Exception as e:
         logger.error('Error : extract_id_from_response\n',e)
         return None
    return 1

def get_change_id(previous_id):
     
    tries = 0

    while(tries < conf['ERROR_TRIES']):

        response_text = get_id_from_url(conf['NEXT_CHANGE_IDS_URL'],conf['URL_HEADERS'])
        if (not response_text):
            logger.error('Error : get_change_id\nResponse_text is empty. Tries = {}\n'.format(tries))
            tries+=1
            continue

        next_change_id = extract_id_from_response(response_text,previous_id)

        if(not next_change_id):
            logger.error('Error : get_change_id\nnext_change_id is empty. Tries = {}\n'.format(tries))
            tries +=1
            continue

        logger.debug('Next_change_id = {}\n'.format(next_change_id))
        
        return next_change_id

def get_change_ids(output_file_name):
    
    count = 0
    previous_id = ""
    
    while(True):

       logger.debug('Getting next change id from api')
       logger.debug('Number : {0}'.format(count))
       
       next_change_id = get_change_id(previous_id)
       if(not next_change_id):
           logger.error('Error : get_change_ids\nCould not retrieve next_change_id')
           continue

       logger.debug('Retun from get_change_id with next_change_id={}'.format(next_change_id))

       
       logger.debug("{:15}{}\n{:15}{}".format('previous_id = ',previous_id,'NextChangeID = ',next_change_id))
       
       result = save_change_id_to_file(output_file_name,next_change_id,count)
       if(not result):
           logger.error('Error : get_change_ids\nCould not write next_change_id to csv file')
           continue

       previous_id = next_change_id
       count+=1

       time.sleep(2)


def main():
    
    if args.dir:
        output_path = os.path.abspath(args.dir[0])
    else:
        output_path = os.path.abspath(conf['OUTPUT_PATH'])
            
    output_file_name = os.path.join(output_path,conf['DEAMON_CSV_NAME'])

    get_change_ids(output_file_name)

if __name__ == "__main__":
    sys.exit(main())
