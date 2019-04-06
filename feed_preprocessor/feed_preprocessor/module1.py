#from boltons.cacheutils import cachedproperty
#import os,json

#class Foo(object):

#    def __init__(self):
#        self.mods = None

#    @cachedproperty
#    def cached_mod(self):
#        if not self.mods[item_category]: 
#            try:
#                new_path = os.path.join('C:\\Users\\Digi\\Desktop\\poe_price_predictor\\pyapp1\\Uniques_Features\\explicit_mods\\Json','{}_explicit_mods.json'.format(item_category))
#                with open(new_path,'r') as f:
#                    mods = json.load(f)
#                    self.mods = mods
#            except Exception as e:
#                print(e)
#        return self.mods


#f = Foo()
#print(f.mods)  # initial value
#print(f.cached_mod('amulet'))  # cached property is calculated
#print(f.cached_mod)  # same value for the cached property - it isn't calculated again
#print(f.mods)  # the backing value is different (it's essentially unrelated value)

#from boltons.cacheutils import cachedproperty

#class Foo(object):
#    def __init__(self):
#        self.value = 4

#    @cachedproperty
#    def cached_prop(self):
#        self.value += 1
#        return self.value


#f = Foo()
#print(f.value)  # initial value
#print(f.cached_prop)  # cached property is calculated
#f.value = 1
#print(f.cached_prop)  # same value for the cached property - it isn't calculated again
#print(f.value)  # the backing value is different (it's essentially unrelated value)
import os,json

class Mods(object):

    def __init__(self,config_file):
        self.mods = None
        try:
            with open(config_file,'r') as f:
                self.conf = json.load(f)['CONFIG']
        except Exception as e:
            print(e)

    def __value__(self):
        return self.mods

    def get_mod(self,mod_category,item_category):
        if not self.mods:
            self.mods = {}
        if mod_category not in self.mods:
            self.mods[mod_category] = {}
        if item_category not in self.mods[mod_category]:
            try:
                mods_dir = self.conf['{}_MODS_DIR'.format(mod_category.upper())]
                file_path = os.path.join(mods_dir,'{}_{}_mods.json'.format(item_category,mod_category))
                with open(file_path,'r') as f:
                    mods = json.load(f)
                    self.mods[mod_category][item_category] = mods
            except Exception as e:
                print(e)
        return self.mods[mod_category][item_category]

