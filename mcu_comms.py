import serial
import json
from enum import Enum
import time
import socket
import sys

START_BYTE = b'\1'
DATA_END_BYTE = b'\2'
CRC_END_BYTE = b'\3'

class ReadSerialState(Enum):
    IDLE = 0
    DATA_READ = 1
    PARSE_MESSAGE = 3

class MCUCommunication:
    """
    A class used to communicate with a microcontroller over serial

    ...

    Attributes
    ----------

    Methods
    -------
    connect(port)
        Connects to specified serial port
    sendCommand(command, payload=None)
        Send JSON command and payload
    readSerial()
        Read byte from serial port and process based on 
        message state and byte type        
    """

    def __init__(self):
        self.expectedReturnCommand = ""

        self.readSerialState = ReadSerialState.IDLE
        self.serialConnected = False

    def connect(self, port):
        try:
            attemptedPort = serial.Serial(port, baudrate=115200)
        except:
            return False
        if attemptedPort.isOpen():
            self.serialPort = attemptedPort
            return True
        return False

    def sendCommand(self, command, payload=None):
        if payload is not None:
            jsonCommand = {"command":command, "payload":payload}
        else:
            jsonCommand = {"command":command, "payload":{}}
        jsonData = json.dumps(jsonCommand).encode('utf-8')

        msgData = START_BYTE + jsonData + DATA_END_BYTE

    def readSerial(self):
        currentSerialString = ""
        start_time = time.time()

        # Process message with 25ms timeout
        while(time.time() - start_time < 0.025):
            # Check if there are any new bytes in serial port
            if self.serialPort.in_waiting:
                # Check what state the serial read is in
                if self.readSerialState == ReadSerialState.IDLE:
                    newByte = self.serialPort.read()
                    if len(newByte) == 1:
                        # Since we're in idle check if new byte is the start byte of a new message
                        if bytes([newByte[0]]) == START_BYTE:
                            self.readSerialState = ReadSerialState.DATA_READ
                
                if self.readSerialState == ReadSerialState.DATA_READ:
                    newByte = self.serialPort.read()
                    if len(newByte) == 1:
                        # If byte is start byte, restart data read with empty string
                        if bytes([newByte[0]]) == START_BYTE:
                            self.readSerialState = ReadSerialState.DATA_READ
                            currentSerialString = ""
                        # If byte is data end byte, end data reading and go to parse message, otherwise, add byte to string
                        elif bytes([newByte[0]]) == DATA_END_BYTE:
                                self.readSerialState = ReadSerialState.PARSE_MESSAGE
                        else:
                            currentSerialString = currentSerialString + bytes([newByte[0]]).decode("utf-8")

                if self.readSerialState == ReadSerialState.PARSE_MESSAGE:
                    self.readSerialState = ReadSerialState.IDLE
                    # check the message integrity
                    print(currentSerialString)
                    return currentSerialString


class MatlabCommunication:
    """
    A class used to communicate with MATLAB script over TCP

    ...

    Attributes
    ----------

    Methods
    -------
    connect(ip='127.0.0.1', port=54320)
        Connects to TCP port, requires MATLAB script to be running
    sendDataJson(command, payload=None)
        Forward JSON received from MCU to TCP port       
    """
    def connect(self, ip='127.0.0.1', port=54320):
        server_port=(ip, port)
        try:
            # create an AF_INET, STREAM socket (TCP)
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except:
            print('Failed to create a socket. ')
            sys.exit()
        print('Socket Created')

        self.sock.connect(server_port)
        print("Client started")
        time.sleep(0.01)

    def sendDataJson(self, data):
        try:
            json.loads(data)
            self.sock.send(data.encode('utf-8'))
        except Exception as e:
            if sys.exc_info()[0] == json.decoder.JSONDecodeError:
                print(f"Invalid JSON: {data}")
            else:
                print(e)
                exit()


if __name__=='__main__':
    mcu = MCUCommunication()
    mcu.connect('COM10')

    matlab = MatlabCommunication()
    matlab.connect()

    while True:
        if mcu.serialPort.in_waiting:
            data = mcu.readSerial()
            matlab.sendDataJson(data)