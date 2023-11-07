import serial
import string
import numpy as np
from time import sleep

#TODO check headers compatibility with number of sensors declared...

class A1324LUA():

    def __init__(self, port, n_sensors, sensitivity):
        """

        Args:
            port (string): port which arduino is connected to
            n_sensors (int): number of sensors
            sensitivity (float): mT/V
        """

        self.port = port
        self.n_sensors = n_sensors
        self.sensitivity = sensitivity
        self.ser = None

    def initialiseSerialCOM(self, baudrate=9600):
        try:
            self.ser = serial.Serial(self.port)
            self.ser.baudrate = baudrate
            self.ser.timeout = 2
            self.ser.write_timeout = 10
            sleep(1)
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
            self.ser.readline() # Used to avoid errors
            sleep(.1)

            # Check if there are enough avaliable sensors
            self.ser.write("CH:AVA?\n".encode())
            sleep(.1)
            max_ava_sensors = self.ser.readline().decode().strip()
            # print(max_ava_sensors)
            if int(max_ava_sensors) < self.n_sensors:
                raise Exception(f"The maximum available sensors is lower than {self.n_sensors}")
            
            # Set number of used sensors
            self.ser.write(f"CH:USE: {self.n_sensors}\n".encode())
            sleep(.1)
            reply = self.ser.readline().decode().strip()
            if int(reply) != self.n_sensors:
                raise Exception("Error in sending the number of used sensors")

            return [True, self.ser.name]
        except Exception as e:
            return [False, str(e)]
    
    def close(self):
        self.ser.close()

    def startMeasure(self):
        try:
            self.ser.reset_input_buffer()
            sleep(0.1)
            headers = list(string.ascii_uppercase)
            meas_values = np.zeros(self.n_sensors)
            self.ser.write("MEAS:ST\n".encode())
            sleep(0.1)
            for _ in range(self.n_sensors):
                data = self.ser.readline()
                # print(data)
                data = data.decode().strip()
                meas_values[headers.index(data[0])] = float(data[1:]) * self.sensitivity # The first character of data defines the header that is used to
                                                                                            #determine the slot of the measurement inside the meas_values list 
            return [True, meas_values]
        except Exception as e:
            return [False, str(e)]
        
if __name__ == "__main__":
    s = A1324LUA("/dev/ttyACM0", 1, 20)
    r = s.initialiseSerialCOM()
    print(r[0])

        