import can
import time
from cantp import CanTp

class TransmitterNode:
    def __init__(self, channel='test', bustype='virtual'):
        # Use Virtual CAN bus
        self.bus = can.interface.Bus(channel=channel, bustype=bustype)
        self.cantp = CanTp(self.bus)
        self.sequence_number = 1

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
