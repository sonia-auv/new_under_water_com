import json

CONFIG_FILE = 'com_config.json'

def read_config_file():
    with open(CONFIG_FILE, 'r') as config:
        config_dict = json.loads(config.read())
    return config_dict

def get_role(auv):
    try:
        roles = read_config_file()['roles']
    except KeyError:
        print('Missing role assignement, default role is "a"')
        return 'a'
    
    try: 
        role = roles[auv] 
    except KeyError:
        print('Malformed role request, default role is "a"')
        return 'a'
        
    return role 

    