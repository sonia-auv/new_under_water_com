import sys
import time
from multiprocessing import Event, Process

from wlmodem import WlModem, WlModemSimulator


class ModemWrapper:
    enc_byteorder = "big"
    enc_pos_shift = 10

    # Set the event to stop the child process
    reception_tread_event = Event()

    def __init__(self, name, role, test=False, test_setup=[]):
        if test:
            self.wlModem = WlModemSimulator(*test_setup)
        else:
            self.wlModem = WlModem()
        self.name = name

        self.ch = 6
        self.role = role
        self.connect_modem()

        self.states_count = 1
        self.pos_coords_count = 3  # Coordinates sent : X, Y, Z
        self.enc_pos_bytes_per_coord = 2  # Bytes per coordinate
        self.enc_pos_bytes = self.enc_pos_bytes_per_coord * self.pos_coords_count # Bytes reserved for the coord
        self.enc_state_bytes = self.wlModem.payload_size - self.enc_pos_bytes  # Bytes reserved for the states
        self.enc_state_bytes_per_state = int(self.enc_state_bytes / self.states_count)
        if self.enc_state_bytes_per_state < 1:
            print("!Warning: not enough bytes left for the states\nExiting...")
            sys.exit(1)

        self.configure()

    '''
    Functions to manage the wlModem 
    '''
    def connect_modem(self):
        print("Connecting to modem %s..." % self.name, end="", flush=True)
        if not self.wlModem.connect():
            print("[FAILED]")
            sys.exit(1)
        print("[DONE]")

    def configure(self):
        print("Configuring modem %s..." % self.name, end="", flush=True)
        if not self.wlModem.cmd_configure(self.role, self.ch):
            print("[FAILED]")
            sys.exit(1)
        print("[DONE]")

    def wait_for_link(self, timeout=10):
        while timeout > 0:
            link_up = self.wlModem.cmd_get_diagnostic().get("link_up")
            print("Link is " + ("UP" if link_up else "down"))
            if link_up:
                return True
            time.sleep(1.0)
            timeout -= 1
        print("Link cannot be established. Did you start the other modem?")
        return False

    '''
    Encoding and decoding
    '''
    def encode_position(self, coords_list):
        encoded_list = []
        for coord in coords_list:
            coord = int(round(coord * self.enc_pos_shift))
            encoded_list.append(
                coord.to_bytes(
                    self.enc_pos_bytes_per_coord, self.enc_byteorder, signed=True
                )
            )
        return encoded_list

    def decode_position(self, coords_bytes):
        decoded_list = []
        for i in range(0, self.enc_pos_bytes, self.enc_pos_bytes_per_coord):
            coord_bytes = coords_bytes[i : i + self.enc_pos_bytes_per_coord]
            dec_coord = int.from_bytes(coord_bytes, self.enc_byteorder, signed=True)
            decoded_list.append(float(dec_coord) / self.enc_pos_shift)
        return decoded_list

    def encode_state(self, state):
        # Make sure the state variabe is a list
        state_list = [state] if not isinstance(state, list) else state

        # Define behaviour for unexpected inputs
        if len(state_list) == 0:
            print("!Warning: No state to encode, expected %d state(s) --> Sending error state" % self.states_count)
            state_list = [-20]
        if len(state_list) > self.states_count:
            print("!Warning: Too many states to encode, encoding only the first %d state(s)" % self.states_count)
            state_list = state_list[: self.states_count]

        # Encode and return states
        enc_state_list = [state.to_bytes(self.enc_state_bytes_per_state, self.enc_byteorder, signed=True) for state in state_list]
        return enc_state_list

    def decode_state(self, state_enc):
        return [int.from_bytes(state_enc, self.enc_byteorder, signed=True)]

    def encode_std_msg(self, msg_list):
        enc_state = self.encode_state(msg_list[: -self.pos_coords_count])
        enc_pos = self.encode_position(msg_list[-self.pos_coords_count :])
        return enc_state + enc_pos

    def decode_std_msg(self, enc_msg):
        # Get the last M state bytes of the N byte message and decode them
        coords_bytes = enc_msg[-self.enc_pos_bytes :]
        coords_list = self.decode_position(coords_bytes)

        # Get the first N-M state bytes of the N byte message and decode them
        state_bytes = enc_msg[: self.enc_state_bytes]
        state = self.decode_state(state_bytes)

        # Return the assembled list
        msg_list = state + coords_list
        return msg_list
    
    '''
    Functions to send and receive messages
    '''
    def send_std_msg(self, msg):
        msg_enc_list = self.encode_std_msg(msg)
        msg_enc = b''.join(msg_enc_list)
        return self.wlModem.cmd_queue_packet(msg_enc)

    def receive_std_msg(self, timeout=5):
        pkt = self.wlModem.get_data_packet(timeout)
        msg_list = None
        if pkt:
            msg_list = self.decode_std_msg(pkt)
        return msg_list

    # def send_std_msg_loop(self, sleep_time=2):
    #     print("Sending packets to other modem. Ctrl-C to abort")
    #     try:
    #         while True:
    #             if self.wlModem.cmd_get_queue_length():
    #                 self.wlModem.cmd_flush_queue()
    #             if self.send_std_msg():
    #                 print("Sent standard message, queue length: %d" % self.wlModem.cmd_get_queue_length(),)
    #             else:
    #                 print("Failed to send message")
    #             time.sleep(sleep_time)
    #     except KeyboardInterrupt:
    #         print("Stopping")

    def receive_std_msg_loop(self):
        print("Waiting for packet from other modem. Ctrl-C to abort")
        try:
            while True:
                pkt = self.receive_std_msg()
                if pkt:
                    print("Got:", pkt)
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("Stopping")

    '''
    Functions to handle separate thread for message reception

    Only works on linux, see 'spwan' vs 'fork':
    https://docs.python.org/3/library/multiprocessing.html#contexts-and-start-methods  
    '''
    def receive_std_msg_process(self):
        while not self.reception_tread_event.is_set():
            pkt = self.receive_std_msg(timeout=0.1)
            if pkt:
                print("Got:", pkt)
            else:
                print("Got no message")
            time.sleep(0.1)
        sys.exit(0)
    
    def start_reception_process(self):
        self.receive_message = Process(target=self.receive_std_msg_process)
        print("Starting new process for message reception...")
        self.receive_message.start()
        return True

    def end_reception_process(self):
        self.reception_tread_event.set()
        self.reception_tread_event.wait(10)
        print("...process for message reception ended")
        return True
