import can
from cantp import CanTp

# When using ValueCAN you just need to change interface from "virtual" to "neovi"
class ReceiverNode:
    def __init__(self, channel='1', interface='neovi', bitrate= 500000):
        #Virtual CAN bus
        self.bus = can.interface.Bus(channel=channel, interface=interface, bitrate=bitrate, receive_own_messages=False)
        self.cantp = CanTp(self.bus)
        
    def receive_message(self):
        consecutive_count = 0  # Number of consecutive received frames
        first_frame_received = False
        received_frames = []
        block_size = 3  # Default block size

        while True:
            message = self.bus.recv(timeout=10)
            if message is not None:
                received_data = self.cantp.process_frame(message.data)

                # If the message is a consecutive frame
                if (message.data[0] & 0xF0) == 0x20:
                    consecutive_count += 1
                    received_frames.append(list(message.data))
                    
                    # Print received consecutive frame immediately
                    
                    # print(f"Received Consecutive Frame {consecutive_count}: {list(message.data)}")

                    # Check if block size has been reached or if it's the last frame
                    remaining_data_length = self.cantp.total_length - len(self.cantp.received_data)
                    if remaining_data_length <= 0:
                        print("Reassembled message successfully!")
                        #Print full Message                      
                        print(f"Full message received (bytes): {self.cantp.received_data.decode()}")
                        print("\n")
                        break

                    if consecutive_count == block_size:
                        # Send Flow Control (CTS) after every 3 consecutive frames or remaining frames
                        print("Sending Flow Control (CTS)...")
                        self.cantp.send_flow_control('CTS', block_size=3)

                        consecutive_count = 0  # Reset counter
                        received_frames.clear()  # Clear buffer
            else:
                print("Timeout waiting for message.")
    
#When use ValueCAN for Transmit and Receive
if __name__ == "__main__":
    receiver = ReceiverNode(channel='1', interface='neovi', bitrate=500000)
    receiver.receive_message()
