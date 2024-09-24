import threading
import time
from Transmiter import TransmitterNode
from Receiver import ReceiverNode

# Use event
stop_event = threading.Event()

def transmitter_thread():
    transmitter = TransmitterNode()
    try:
        while not stop_event.is_set():  
            message_data = bytearray([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58]) 
            print("Transmitting message...")
            transmitter.send_message(message_data)
            time.sleep(3)  # Sent message after every seconds
    except KeyboardInterrupt:
        print("Transmitter thread stopped.")

def receiver_thread():
    receiver = ReceiverNode()
    try:
        while not stop_event.is_set():  # Check if stop_event will set
            print("Waiting to receive message...")
            receiver.receive_message()
            time.sleep(3) # Time Sleep
    except KeyboardInterrupt:
        print("Receiver thread stopped.")

if __name__ == "__main__":
    t1 = threading.Thread(target=transmitter_thread, daemon=True)
    t2 = threading.Thread(target=receiver_thread, daemon=True)

    t1.start()
    t2.start()

    try:
        # Execute main function when run thread
        while t1.is_alive() and t2.is_alive():
            time.sleep(3)
    except KeyboardInterrupt:
        print("Stopping threads...")
        stop_event.set()  # Stop thread
        t1.join()
        t2.join()
        print("Threads stopped.")
