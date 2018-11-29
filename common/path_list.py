from common import api_func

def get():

    reg_path_list = []

    reg_path_list.append({'method':'GET', 'func':'/make_call_auto', 'handler':api_func.make_call_auto})

    return reg_path_list

