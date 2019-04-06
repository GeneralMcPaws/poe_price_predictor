import Lazy_Mods
import logging
class Full_Feature_Recorder(object):
    """description of class"""

    def __init__(self,conf):
        self.logger = logging.getLogger('file_console_logger')
        try:
            self.conf = conf
        except Exception as e:
            print(e)
        self.lazy_mods = Lazy_Mods.Lazy_Full_Mods(conf)

    def create_full_record(self,incomplete_input_record_dic):

        try:
            #get the full_record to fill up
            item_category = incomplete_input_record_dic["item_category"]
            league = incomplete_input_record_dic["league"]
            item_rarity = incomplete_input_record_dic["rarity"]
            rarity = 'unique' if item_rarity is 3 else 'rare'

            complete_record = self.lazy_mods.get_full_mod(league,rarity,item_category).copy()
            for key in incomplete_input_record_dic:
                if key == 'explicit_mods':
                    for gen_mod in incomplete_input_record_dic['explicit_mods']:
                        mod_value,mod_gen_name = self.get_gen_mod_values(gen_mod,'ex_')
                        complete_record[mod_gen_name] = mod_value
                    continue
                if key == 'implicit_mods':
                    for gen_mod in incomplete_input_record_dic['implicit_mods']:
                        mod_value,mod_gen_name = self.get_gen_mod_values(gen_mod,'im_')
                        complete_record[mod_gen_name] = mod_value
                    continue
                if key == 'enchantment_mod':
                    gen_mod = incomplete_input_record_dic['enchantment_mod']
                    mod_value, mod_gen_name = self.get_gen_mod_values(gen_mod, 'en_')
                    complete_record[mod_gen_name] = mod_value
                    #for gen_mod in incomplete_input_record_dic['enchantment_mods']:
                    #    mod_value,mod_gen_name = self.get_gen_mod_values(gen_mod,'en_')
                    #    complete_record[mod_gen_name] = mod_value
                    continue
                if key == 'corrupted_mods':
                    for gen_mod in incomplete_input_record_dic['corrupted_mods']:
                        mod_value,mod_gen_name = self.get_gen_mod_values(gen_mod,'co_')
                        complete_record[mod_gen_name] = mod_value
                    continue
                if key in complete_record:
                    try:
                        complete_record[key] = float(incomplete_input_record_dic[key])
                    except Exception as e:
                        complete_record[key] = incomplete_input_record_dic[key]
            return complete_record

        except KeyError as e:
            self.logger.error("ERROR : input_record does not have the required fields -{}-".format(e))
            return None
        except Exception as e:
            self.logger.error("ERROR : trying to create full_feature_record -{}-".format(e))
            return None

    def get_gen_mod_values(self,gen_mod : str, mod_type : str):
        split_mod = gen_mod.split('_')
        if '+' in split_mod[1]: split_mod[1] = split_mod[1][1:]
        try:
        	mod_value = 1 if split_mod[1] =='None' else float(split_mod[1])
        except Exception as e:
        	mod_value = split_mod[1]
        mod_gen_name =  mod_type + split_mod[2]

        return mod_value,mod_gen_name
