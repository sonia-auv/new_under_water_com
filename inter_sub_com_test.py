import time
import timeit

from inter_sub_com import role_dict
from modemWrapperClass import ModemWrapper

auv = 'AUV8'
position_XYZ = [12.324, 23.234, -5.098]
modem = ModemWrapper(auv, role_dict[auv], True, [0 ,0, 0])
start_time = time.time()
modem.wait_for_link(5)


def encoding_duration():
    print('Average message encode time: %0.2f ms'% timeit.timeit('modem.encode_std_msg([3]+position_XYZ)', globals=globals(), number=1000))

def test_mutliprocessing(sleep_time):
    modem.start_reception_process()
    print('Main process: Going to sleep...')
    time.sleep(sleep_time)
    print('Main process: killing child thread...')
    modem.end_reception_process()

def real_world_com_test():
    modem.start_reception_process()
    try: 
        while True:
            msg = get_state() + get_position()
            modem.wlModem.cmd_flush_queue()
            modem.send_std_msg(msg)
            print('Sent message')
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    modem.end_reception_process()
    modem.receive_message.join()


def get_position():
    # Currently just a place holder for ROS call
    return [12.324, 23.234, -3.098]

def get_state():
    # Currently just a place holder for ROS call
    return [int(time.time() - start_time)]


if __name__ == "__main__":
    real_world_com_test()



# success = modem.send_std_msg([3]+position_XYZ)
# if not success:
#    sys.exit(0)

# #test_mutliprocessing(5)
# real_world_com_test()