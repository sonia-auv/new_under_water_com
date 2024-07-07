from src.modemWrapperClass import ModemWrapper 
from test.inter_sub_com_test import real_world_com_test
from config.config_interface import get_role

def test_mode():
    auv = 'AUV8'
    role = get_role(auv)
    modem = ModemWrapper(auv, role, False, [0 ,0, 0])
    return modem.wait_for_link(5)
   #real_world_com_test(modem)

print(test_mode())
