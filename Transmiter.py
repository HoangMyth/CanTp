import can
import ics
import time
from cantp import CanTp

# When using ValueCAN you just need to change interface from "virtual" to "neovi"

class TransmitterNode:
    def __init__(self, channel='1', interface='virtual', bitrate = 500000):
        # Use Virtual CAN bus
        self.bus = can.interface.Bus(channel=channel, interface=interface, bitrate=bitrate)
        self.cantp = CanTp(self.bus)
        self.sequence_number = 1
        
    def __enter__(self):
        # When use 'with', __enter__ called
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        # When End 'with', __exit__ is called
        self.bus.shutdown()
        print("CAN bus connection closed.")

    def send_message(self, data):
        frames = self.cantp.fragment(data)

        if len(frames) == 1:
            # If data have 1 frame (Single Frame)
            print(f"Sending Single Frame: {frames[0]}")
            message = can.Message(arbitration_id=0x123, data=frames[0], is_extended_id=False)
            self.bus.send(message)
            print("Single Frame sent, transmission complete.")
        else:
            # Sent First Frame
            print(f"Sending First Frame: {frames[0]}")
            first_frame = can.Message(arbitration_id=0x123, data=frames[0], is_extended_id=False)
            self.bus.send(first_frame)
            self.sequence_number = 1

            # Waiting receiver First Frame and send Flow Control
            print("Waiting for Flow Control after First Frame...")

            flow_control = self.bus.recv(timeout=2)  
            if flow_control is not None:
                print(f"Received Flow Control: {list(flow_control.data)}")

                if flow_control.data[0] & 0x0F == 0x00:  # If Continue To Send (CTS)
                    block_size = flow_control.data[1]  # Take block size từ Flow Control
        
                    # Send countinuously Consecutive Frames equa block size
                    frame_count = 0
                    for i in range(1, len(frames)):
                        frame = frames[i]
                        frame[0] = 0x20 | (self.sequence_number & 0x0F)  # Determine frame type and count
                        print(f"Sending Consecutive Frame: {frame}")
                        consecutive_frame = can.Message(arbitration_id=0x123, data=frame, is_extended_id=False)
                        self.bus.send(consecutive_frame)
                        self.sequence_number += 1
                        frame_count += 1
                        time.sleep(0.05) 

                        if frame_count == block_size:
                            frame_count = 0  # Reset number of Frame send
                            # print("Waiting for next Flow Control...")
                            flow_control = self.bus.recv(timeout=2)
                            if flow_control is None or flow_control.data[0] & 0x0F != 0x00:
                                 print("No more Flow Control received or stopped.")
                                 break
            else:
                print("No Flow Control received, stopping transmission.")

#When use ValueCAN for Transmit and Receive
if __name__ == "__main__":
    with TransmitterNode(channel='1', interface='neovi', bitrate=500000) as transmitter:
        # input_string = input("Ennter Your Data: \n")
        # message_data = bytearray(input_string.encode('utf-8'))
        message_data = bytearray([1, 2, 3, 4, 5, 6, 7, 8, 9, 10,11,12,13,14,15,16,17,18,19,20,21])  # Dữ liệu truyền vào
        transmitter.send_message(message_data)
        # transmitter.bus.shutdown()