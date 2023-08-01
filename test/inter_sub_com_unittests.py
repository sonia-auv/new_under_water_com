import unittest
from math import log10

from inter_sub_com import role_dict
from modemWrapperClass import ModemWrapper


class TestRoles(unittest.TestCase):
    
    def test_role_auv7(self):
        self.assertEqual(role_dict['AUV7'], 'b') 

    def test_role_auv8(self):
        self.assertEqual(role_dict['AUV8'], 'a') 


class SimulationTestCase(unittest.TestCase):
    def setUp(self):
        self.auv = 'AUV8'
        self.link_up_duration = 0
        self.queue_duration = 1
        self.next_duration = 0
        self.modem = ModemWrapper(self.auv, role_dict[self.auv], True,[self.link_up_duration, self.queue_duration, self.next_duration])
        self.default_position_XYZ = [12.324, 23.234, -3.098]
        self.default_state = [42]
        self.pos_precision = int(log10(self.modem.enc_pos_shift))

        
    def test_link_up(self):
        self.assertTrue(self.modem.wait_for_link(self.link_up_duration+2))
        
    def test_std_message(self):
        success = self.modem.send_std_msg(self.default_state + self.default_position_XYZ)
        self.assertTrue(success)
        response_list = self.modem.receive_std_msg(self.queue_duration+2)
        self.assertEqual( self.default_state,response_list[:self.modem.states_count] )
        rounded_coords = [round(elem, self.pos_precision) for elem in self.default_position_XYZ]
        self.assertEqual(rounded_coords, response_list[-self.modem.pos_coords_count:])

    def test_too_many_states_message(self):
        new_states = [23, 4, 34, 5]
        success = self.modem.send_std_msg( new_states + self.default_position_XYZ)
        self.assertTrue(success)
        response_list = self.modem.receive_std_msg(self.queue_duration+2)
        self.assertEqual( new_states[:self.modem.states_count] ,response_list[:self.modem.states_count] )
        rounded_coords = [round(elem, self.pos_precision) for elem in self.default_position_XYZ]
        self.assertEqual(rounded_coords, response_list[-self.modem.pos_coords_count:])
    