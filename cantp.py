import can
import time

class CanTp:
    def __init__(self, bus):
        self.sequence_number = 0
        self.received_data = bytearray()
        self.total_length = 0
        self.bus = bus

    def fragment(self, data):
        frames = []
        data_length = len(data)
        
        if len(data) <= 7:  # Single Frame
            pci_byte = 0x00 | data_length
            frames.append([pci_byte] + list(data))  # Single Frame
        else:
            # First Frame
            pci_higherbit = 0x10 | (data_length >> 8)
            pci_lowerbit = data_length & 0xFF
            frames.append([pci_higherbit, pci_lowerbit] + list(data[:6]))
            data = data[6:]

            # Consecutive Frames
            while data:
                self.sequence_number += 1
                frames.append([0x20 | (self.sequence_number & 0x0F)] + list(data[:7]))
                data = data[7:]

        return frames
    
    def process_frame(self, frame):
        pci_type = (frame[0] & 0xF0) >> 4  # Type frame: single frame, first frame, consecutive frame

        if pci_type == 0x0:  # Single Frame
            length = frame[0] & 0x0F
            self.received_data.extend(frame[1:1 + length])
            return True
        
        elif pci_type == 0x1:  # First Frame
            self.total_length = ((frame[0] & 0x0F) << 8) + frame[1]
            self.received_data = bytearray()
            self.received_data.extend(frame[2:8])
            self.sequence_number = 1

            print(f"First Frame received, total length of Data is: {self.total_length}. Sending Flow Control...")
            self.send_flow_control('CTS', block_size=3)  # Sent Flow Control with block size is 3
            return False  # Not receive enough
        
        elif pci_type == 0x2:  # Consecutive Frame (CF)
            # Check Numberical of CF
            seq_num = frame[0] & 0x0F  # Take numberical
            if seq_num != self.sequence_number:
                print(f"Error: Expected sequence number {self.sequence_number}, but got {seq_num}")
                return False  # False
            
            # Merge data from CF
            self.received_data.extend(frame[1:8])
            self.sequence_number += 1  # Increase the order number
            
            # Check Data received enough
            if len(self.received_data) >= self.total_length:
                print("Reassembled message successfully!")
                return True  # Enough data received

        return False  # Not enough data received
    
    def send_flow_control(self, control_type, block_size=3, st_min=0):
        #Sent FlowCon trol
        if control_type == 'CTS':
            flow_status = 0x00  # Continue to Send
        elif control_type == 'WAIT':
            flow_status = 0x01  # Wait
        elif control_type == 'OVFLW':
            flow_status = 0x02  # Overflow

        # Byte #1: PCI byte for Flow Control
        pci_byte = 0x30 | flow_status 
        # Byte #2: Block Size (BS)
        block_size = block_size & 0xFF  # Block size max 255
        # Byte #3: Separation Time Minimum (STmin)
        st_min = st_min & 0xFF  # STmin max 255 ms

        # Tạo frame Flow Control
        flow_control_frame = [pci_byte, block_size, st_min] + [0x00, 0x00, 0x00]  # other byte is N/A

        # Gửi frame Flow Control
        message = can.Message(arbitration_id=0x7DF, data=flow_control_frame, is_extended_id=False)
        self.bus.send(message)
        print(f"Sent Flow Control frame: {flow_control_frame}")
    
    def reassemble(self):
        return self.received_data.decode('utf-8', errors='ignore')
