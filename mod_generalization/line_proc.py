from config import Config

def process_params(new_line,number_groups,case):
    params = []

    #case = 1 -> only one number present in line
    #case = 2 -> 2 numbers present in line
    for i in range(case):
        param = {'pos':'','type':'','value':''}
        param['pos'] = i
        if(Config.RANGE_REGEX.search(number_groups[i])):
            param['type'] = 'R'
            param['value'] = ''
        else:
            param['type'] = 'D'
            param['value'] = number_groups[i]
        params.append(param)
    return params

def process_line(org_line,number_groups,case):
    
    attribute = {'gen':'','org':[],'params':[]} 
    attribute['org'].append(org_line)

    output_line = ''

    if (case == 0 or case == 3):         #we found no groups or we found 3 number_groups
        attribute['gen'] = ''
        attribute['params'] = []
        output_line = org_line + '\n'
    elif (case == 2):
        new_line = Config.LINE_REGEX.subn(r'\1#\3#\5', org_line)[0]
        attribute['gen'] = new_line
        attribute['params'] = process_params(new_line,number_groups, case)
        output_line = new_line + '\n'
    else:
        new_line = Config.LINE_REGEX.subn(r'\1#\3', org_line)[0]
        attribute['gen'] = new_line
        attribute['params'] = process_params(new_line,number_groups, case)
        output_line = new_line + '\n'

    return attribute, output_line