#ARGUMENTS
# 1. file with lines you want to process or directory with files you want to process
# 2. extension(s) of files
# 4. logging files
# 5. config file
# 6. output directory

import sys,re,os,json,io
import line_proc
from config import Config
import pathlib
import argparse
import glob
import output_handler
import re

def extract_features(file_name,file_name_json):
    data = {}
    try: 
        org_file = open(file_name,'r',errors='ignore')
        for line in org_file:
            #attribute = {'gen':'','org':'','params':[]}      #instansiate the new attribute
            #line = line[:-1] if line[-1]=='\n' else line     #remove newLine character at end of string
            line = line.strip(' \n\t').lower()                #remove newLines and tab characters at end of string

            attribute = process_generalized_line(line)
            
            hashKey = attribute['gen']

            if hashKey in data:
                continue
            data[hashKey] = attribute

        with open(file_name_json,'w') as fJSON:
            fJSON.write(json.dumps(data,indent=4,sort_keys=True))
        org_file.close()
    except IOError as ioe:
        org_file.close()
        print('Error while trying to open file')
        raise(ioe)
    except Exception as e:
        org_file.close()
        raise(e)

def hasNumbers(input):
    return bool(re.search(r'\d',input))

def process_generalized_line(line):

    attribute = {
        'gen':line,
        'org':[],
        'params':[]}

    #if hasNumbers(line):
        

    if '#' in line:
        attribute['params'].append({
                                    'pos':0,
                                    'type':'R',
                                    'value':''})
        return attribute

    attribute['gen'] = line
    attribute['org'] = line
    return attribute



parser = argparse.ArgumentParser(description='This program produces a json file and a regex '+
                                 'from a file containing available mods for items')

group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("-d","--dir",help="Input the directory/ies in which all the items you wish to process are stored",nargs='+')
group.add_argument("-f","--files",help="File(s) to check",nargs='+')
parser.add_argument('-e','--ext',help="Extensions of files to check",nargs='+',choices=['.txt'],default=['.txt'])
parser.add_argument('-l','--log',help="Logging configuration file")
parser.add_argument('-c','--config',help="Config file")
parser.add_argument('-o','--output',help="Output directory")

args = parser.parse_args()

files_to_process = []

#for option -d : input given is a directory or multiple
if args.dir:
    #for each given directory in the list check if it actually is a directory
    for d in args.dir:
        if not os.path.isdir(d):
            msg = '{0} is not a directory'.format(d)
            raise argparse.ArgumentTypeError(msg)
        #and if there are any files underneath it
        if not glob.glob(d+'*'):
            msg = '{0} directory has no files in it'.format(d)
            raise argparse.ArgumentTypeError(msg)
        #gather all files that you want to process
        directory_files = glob.glob(d+'*')
        for f in directory_files:
            #check if f is a file because glob.glob also returns directories
            if(not os.path.isfile(f)):
                continue
            #check for correct extension
            if any(ext not in os.path.splitext(f)[1] for ext in args.ext):
                msg = "File {0} does not have an extension that belongs in corresponding extension list".format(f)
                print(msg)
                continue
            files_to_process.append(f)

#for option -f : input give is a file or multiple files
if args.files:
    for f in args.files:
        #check for every file if it is indeed a file
        if not os.path.isfile(f):
            msg = '{0} is not a file'.format(f)
            raise argparse.ArgumentTypeError(msg)
        #and then check if its extension is allowed to be processed
        if any(ext not in os.path.splitext(f)[1] for ext in args.ext):
            print(os.path.splitext(f)[1])
            msg = "File {0} does not have an extension that belongs in corresponding extension list".format(f)
            print(msg)
            continue
        files_to_process.append(f)

for file_name in files_to_process:
    file_name_regex,file_name_json = output_handler.create(args.output,file_name)
    extract_features(file_name,file_name_json)
    print('{} processed'.format(file_name))
