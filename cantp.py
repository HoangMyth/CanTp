import can
import time
from enum import Enum

#Define control type for FlowControl
CTS                     = 0x00
WAIT                    = 0x10
OVFLW                   = 0x20

#Define Frame type
class FrameType(Enum):
    SINGLE_FRAME        = 0x00
    FIRST_FRAME         = 0x10
    CONSECUTIVE_FRAME   = 0x20
    FLOW_CONTROL        = 0X30
    
#Define CanType
class CanType(Enum):
    CAN_2_0             = 0
    CAN_FD              = 1
    
class CanTp:
    def __init__(self, bus, can_type=CanType.CAN_FD):
        self.sequence_number = 0
        self.received_data = bytearray()
        self.total_length = 0
        self.bus = bus
        self.can_type = can_type
        self.buffer_size = 50 
        self.current_data_size = 0

    def fragment(self, data):
        frames = []
        if isinstance(data, str):
            data = bytearray(data.encode('utf-8'))
        data_length = len(data)
        
        if self.can_type == CanType.CAN_2_0:
            if data_length <= 7:  # Single Frame
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
                    self.sequence_number %= 16
                    
                    frame_data = list(data[:7])
                    
                    # If last consecutive frame not enough 7 byte, add padding
                    if len(frame_data) < 7:
                        frame_data += [0x00] * (7 - len(frame_data))
                    
                    frames.append([0x20 | (self.sequence_number & 0x0F)] + frame_data)
                    data = data[7:]
                    
        elif self.can_type == CanType.CAN_FD:
            # Used CAN FD
            if data_length <= 63:  # Single Frame
                pci_byte = 0x00 | data_length
                frames.append([pci_byte] + list(data))  # Single Frame
            else:
                # First Frame
                pci_higherbit = 0x10 | (data_length >> 8)
                pci_lowerbit = data_length & 0xFF
                frames.append([pci_higherbit, pci_lowerbit] + list(data[:6]))  # CAN FD First Frame can contain 62 bytes
                data = data[6:]

                # Consecutive Frames
                while data:
                    self.sequence_number += 1
                    frame_data = list(data[:63])
                    
                    # Padding to last Consecutive frame
                    if len(frame_data) < 63:
                        frame_data += [0x00] * (63 - len(frame_data))
                    
                    frames.append([0x20 | (self.sequence_number & 0x0F)] + frame_data)
                    data = data[63:]

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
            
            if self.can_type == CanType.CAN_2_0:
                self.received_data.extend(frame[2:8])  # CAN 2.0 First Frame contain 6 byte
            elif self.can_type == CanType.CAN_FD:
                self.received_data.extend(frame[2:64])  # CAN FD First Frame contain 62 byte

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
            if self.can_type == CanType.CAN_2_0:
                self.received_data.extend(frame[1:8])  # CAN 2.0 Consecutive Frame can contain 7 byte
            elif self.can_type == CanType.CAN_FD:
                self.received_data.extend(frame[1:64])  # CAN FD Consecutive Frame can contain 63 byte

            self.sequence_number += 1  # Increase the order number
            self.sequence_number %= 16  # Reset sequence number về 0 when achieve 15
            
            # Check Data received enough
            if len(self.received_data) >= self.total_length:
                # print("Reassembled message successfully!")
                return True  # Enough data received

        return False  # Not enough data received
    
    def send_flow_control(self, control_type, block_size=3, st_min=250):
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

        # Creat frame Flow Control
        flow_control_frame = [pci_byte, block_size, st_min] + [0x00, 0x00, 0x00]  # other byte is N/A

        # Send frame Flow Control
        if self.can_type == CanType.CAN_FD:
            message = can.Message(arbitration_id=0x123, data=flow_control_frame, is_extended_id=False, is_fd=True)
        else:
            message = can.Message(arbitration_id=0x123, data=flow_control_frame, is_extended_id=False, is_fd=False)

        self.bus.send(message)
        print(f"Sent Flow Control frame: {flow_control_frame}")
    
    def reassemble(self):
        return self.received_data.decode('utf-8', errors='ignore')
