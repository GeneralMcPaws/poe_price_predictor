import json,os
import logging

class Mods(object):
    """description of class"""
    '''Class holding the mods of items following the lazy pattern implementation'''
    
    def __init__(self,conf):
        self.mods = {}
        self.logger = logging.getLogger('file_console_logger')
        try:
            self.conf = conf
        except Exception as e:
            print(e)

    def __value__(self):
        return self.mods
    
    def get_mod(self,mod_category,item_category,league):
        
        if mod_category not in self.mods:
            self.mods[mod_category] = {}
        if item_category not in self.mods[mod_category]:
            try:
                key = '{}_MODS_DIR'.format(mod_category.upper())
                mods_dir = (self.conf[key]).format(league)
                #if 'rare' or 'unique' in mod_category: 
                #    file = mod_category.split('_')[1]
                #    file_path = os.path.join(mods_dir,'{}_{}_mods.json'.format(item_category,file))
                #else:
                file_path = os.path.join(mods_dir,'{}_{}_mods.json'.format(item_category,mod_category))
                with open(file_path,'r') as f:
                    mods = json.load(f)
                    self.mods[mod_category][item_category] = mods
            except Exception as e:
                print(e)
        return self.mods[mod_category][item_category]


