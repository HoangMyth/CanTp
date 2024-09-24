import can
from cantp import CanTp

class ReceiverNode:
    def __init__(self, channel='test', bustype='virtual'):
        #Virtual CAN bus
        self.bus = can.interface.Bus(channel=channel, bustype=bustype)
        self.cantp = CanTp(self.bus)

    def receive_message(self):
        consecutive_count = 0  # Number of consecutive reveive
        first_frame_received = False
        received_frames = []
        while True:
            message = self.bus.recv(timeout=1)
            if message is not None:
                received_data = self.cantp.process_frame(message.data)

                if (message.data[0] & 0xF0) == 0x20:
                    consecutive_count += 1
                    received_frames.append(list(message.data))
                 # Wait until 3 consecutive number to print the information
                    if consecutive_count == 3:
                        for i, frame in enumerate(received_frames):
                            print(f"Received Consecutive Frame {i+1}: {frame}")
                        print("Sending Flow Control (CTS) after receiving 3 CF...")
                        self.cantp.send_flow_control('CTS', block_size=3)
                        consecutive_count = 0  # Reset counter
                        received_frames.clear()  # Clear buffer
            else:
                print("Timeout waiting for message.")
