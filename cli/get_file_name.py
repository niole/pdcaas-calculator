import re

"""
gets the name of the json file
"""
def get_file_name(inpath, new_suffix):
    file_name_p = r'(\w+)\.json'
    file_name_w_ext = inpath.split('/')[-1]

    m = re.match(file_name_p, file_name_w_ext)

    return f'{m.groups()[0]}{new_suffix}.json'
