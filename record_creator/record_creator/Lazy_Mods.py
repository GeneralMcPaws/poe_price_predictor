import json,os
import logging

class Lazy_Full_Mods(object):
    """description of class"""
    '''Class holding the concatenated mods of items following the lazy pattern implementation'''
    
    def __init__(self,conf):
        self.mods = {}
        self.logger = logging.getLogger('file_console_logger')
        try:
            self.conf = conf
        except Exception as e:
            print(e)

    def __value__(self):
        return self.mods
    
    def get_full_mod(self,league,rarity,item_category):
        
        if rarity not in self.mods:
            self.mods[rarity] = {}
        if item_category not in self.mods[rarity]:
            try:
                key = '{}_CONCATENATED_MODS_DIR'.format(rarity.upper())
                mods_dir = (self.conf[key]).format(league)
                file_path = os.path.join(mods_dir,'{}_concatenated_mods.json'.format(item_category))
                with open(file_path,'r') as f:
                    full_mods = json.load(f)
                    self.mods[rarity][item_category] = full_mods
            except Exception as e:
                print(e)
        return self.mods[rarity][item_category]


