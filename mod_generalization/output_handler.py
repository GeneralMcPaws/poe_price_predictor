from os import path as p
from config import Config
import pathlib

def create(output_dir,file_name):

    filename_w_ext = p.splitext(p.basename(file_name))[0]
    
    if output_dir:
        directory_path = p.abspath(output_dir) 
    else:
        directory_path = p.dirname(p.realpath(file_name))

    directory_path_regex = p.join(directory_path,Config.REGEX_FOLDER_NAME)
    directory_path_json = p.join(directory_path,Config.JSON_FOLDER_NAME)
        
    pathlib.Path(directory_path_regex).mkdir(parents=True, exist_ok=True) 
    pathlib.Path(directory_path_json).mkdir(parents=True, exist_ok=True)

    file_name_regex = p.join(directory_path_regex,filename_w_ext) +'_REGEX.txt'
    file_name_json = p.join(directory_path_json,filename_w_ext) +'.json'

    return file_name_regex,file_name_json
