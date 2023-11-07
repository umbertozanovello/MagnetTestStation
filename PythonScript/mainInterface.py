import sys
import glob
from PyQt6.QtWidgets import (QLineEdit, QPushButton, QApplication,
    QVBoxLayout, QHBoxLayout, QDialog, QGroupBox, QLabel, QSpinBox,QDoubleSpinBox, QComboBox, QMessageBox)
from PyQt6.QtCore import Qt, QSize, QThread, QTime, QDate
import a1324lua
import measurementJob
import numpy as np
from functools import partial
import os.path

class MainInterface(QDialog):

    def __init__(self, parent=None):
        super(MainInterface, self).__init__(parent)
        
        self.isConnected = False # True if Arduino is connected
        self.isRunning = False # True if a measurement is running
        self.serialObj = None # The serial instrument instance
        self.zeros = None # List of the zeros for the magentic field measurements
        self.lastMeasured = None # List of last meauserd values
        self.log = None # File handler of the log
        self.measurementThread = QThread()

        self.setWindowTitle("Magnet Test Station - User Interface")

        # Options Group

        optionGroup = QGroupBox("Options")
        n_stations_label = QLabel("N° Stations:")
        sensitivity_label = QLabel("Sensitivity (mT/V):")
        serialPort_label = QLabel("Serial Port:")
        filename_label = QLabel("Log File:")
        
        self.n_stations = QSpinBox()
        self.n_stations.setRange(1,4)
        self.n_stations.valueChanged.connect(self.setMeasLayout)

        self.sensitivity = QDoubleSpinBox()
        self.sensitivity.setRange(0,100.)
        self.sensitivity.setValue(20.)

        if sys.platform.startswith('win'):
            ports = ['COM%s' % (i + 1) for i in range(10)]
        elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
            # this excludes your current terminal "
            ports = glob.glob('/dev/tty[A]*')

        self.serialPort = QComboBox()
        [self.serialPort.addItem(r) for r in ports]

        self.filename = QLineEdit()

        option_HLayout1 = QHBoxLayout()
        option_HLayout1.addWidget(n_stations_label)
        option_HLayout1.addWidget(self.n_stations)

        option_HLayout2 = QHBoxLayout()
        option_HLayout2.addWidget(sensitivity_label)
        option_HLayout2.addWidget(self.sensitivity)

        option_HLayout3 = QHBoxLayout()
        option_HLayout3.addWidget(serialPort_label)
        option_HLayout3.addWidget(self.serialPort)
        
        option_HLayout4 = QHBoxLayout()
        option_HLayout4.addWidget(filename_label)
        option_HLayout4.addWidget(self.filename)

        option_HLayout = QHBoxLayout()
        option_HLayout.addLayout(option_HLayout1)
        option_HLayout.addStretch()
        option_HLayout.addLayout(option_HLayout2)
        option_HLayout.addStretch()
        option_HLayout.addLayout(option_HLayout3)

        option_VLayout = QVBoxLayout()
        option_VLayout.addLayout(option_HLayout)
        option_VLayout.addLayout(option_HLayout4)

        optionGroup.setLayout(option_VLayout)

        # Measurement Group
        self.measGroup = QGroupBox("Measurements")

        self.measResult_labels = []
        self.zero_buttons = []
        self.store_buttons = []
        self.connect_button = QPushButton("Connect")
        self.connect_button.setFixedSize(QSize(200,50))
        self.connect_button.pressed.connect(self.serialConnection)
        self.startMeasure_button = QPushButton("Start Measurement")
        self.startMeasure_button.setFixedSize(QSize(200,50))
        self.startMeasure_button.pressed.connect(self.startStopMeasurement)

        # Main Windows

        self.mainLayout = QVBoxLayout()
        self.mainLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        # self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.addWidget(optionGroup)

        self.setMeasLayout()

    def setMeasLayout(self):
        self.mainLayout.removeWidget(self.measGroup)
        self.measGroup = QGroupBox("Measurements")
        meas_HLayout = QHBoxLayout()
        self.measResult_labels = []
        self.zero_buttons = []
        self.store_buttons = []
        for n in range(self.n_stations.value()):
            station_label = QLabel(f"Test Station {n+1}:")
            station_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            measResult_label = QLabel("--")
            measResult_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            zero_button = QPushButton("Zero")
            zero_button.setFixedSize(QSize(100,50))
            zero_button.pressed.connect(partial(self.setZero,n))
            zero_button.setEnabled(False)
            store_button = QPushButton("Store")
            store_button.setFixedSize(QSize(100,50))
            store_button.pressed.connect(partial(self.storeResult,n))
            store_button.setEnabled(False)

            self.measResult_labels.append(measResult_label)
            self.zero_buttons.append(zero_button)
            self.store_buttons.append(store_button)

            station_VLayout = QVBoxLayout()
            station_VLayout.addWidget(station_label)
            station_VLayout.addWidget(measResult_label)
            station_VLayout.addWidget(zero_button)
            station_VLayout.addWidget(store_button)

            meas_HLayout.addLayout(station_VLayout)
        
        self.measGroup.setLayout(meas_HLayout)
        
        self.mainLayout.addWidget(self.measGroup)

        connAndMeasLayout = QHBoxLayout()
        connAndMeasLayout.addWidget(self.connect_button, 0, Qt.AlignmentFlag.AlignHCenter)
        connAndMeasLayout.addWidget(self.startMeasure_button, 0, Qt.AlignmentFlag.AlignHCenter)
        self.mainLayout.addLayout(connAndMeasLayout)

        self.setLayout(self.mainLayout)

        return
    
    def serialConnection(self):

        if not self.isConnected:
            self.serialObj = a1324lua.A1324LUA(str(self.serialPort.currentText()), self.n_stations.value(), self.sensitivity.value())
            res = self.serialObj.initialiseSerialCOM()
            if res[0]:
                QMessageBox.information(self, "Success", "Succesfully connected:\n"+res[1], QMessageBox.StandardButton.Ok)
                self.isConnected = True
                self.connect_button.setText("Disconnect")
                self.serialPort.setEnabled(False)
                self.n_stations.setEnabled(False)
                self.sensitivity.setEnabled(False)
                self.zeros = np.zeros(self.n_stations.value())
            else:
                QMessageBox.critical(self, "Failure", "Failed to connected:\n"+res[1], QMessageBox.StandardButton.Ok)
        else:
            self.serialObj.close()
            self.serialObj = None
            self.isConnected = False
            self.connect_button.setText("Connect")
            self.serialPort.setEnabled(True)
            self.n_stations.setEnabled(True)
            self.sensitivity.setEnabled(True)


    def startStopMeasurement(self):
        if not self.isConnected:
            QMessageBox.critical(self, "Not Ready", "No device is connected for measurements. Please,"\
                                  "connect a device first and press the connect button", QMessageBox.StandardButton.Ok)
            return
        if not self.isRunning:
            if not self.createLogFile()[0]:
                QMessageBox.critical(self, "Log File", "Issues in Log file creation or opening. Please,"\
                                  "check the Log filename", QMessageBox.StandardButton.Ok)
                return
            self.startMeasure_button.setText("Stop Measurements")
            self.filename.setEnabled(False)
            self.sensitivity.setEnabled(False)
            self.connect_button.setEnabled(False)
            for zero_button, store_button in zip(self.zero_buttons, self.store_buttons):
                zero_button.setEnabled(True)
                store_button.setEnabled(True)
            self.isRunning = True
            self.measurementJob = measurementJob.MeasurementJob(self.serialObj)
            self.measurementJob.measAvailable.connect(self.updateMeasurementLabels)
            self.measurementJob.moveToThread(self.measurementThread)
            self.measurementThread.started.connect(self.measurementJob.run)
            self.measurementThread.start()
        else:
            self.startMeasure_button.setText("Start Measurements")
            self.filename.setEnabled(True)
            self.sensitivity.setEnabled(True)
            self.connect_button.setEnabled(True)
            for zero_button, store_button in zip(self.zero_buttons, self.store_buttons):
                zero_button.setEnabled(False)
                store_button.setEnabled(False)
            self.isRunning = False
            self.measurementJob.stopMeasuring = True
            self.measurementThread.terminate()
            self.measurementThread.wait()
            self.measurementJob = None
            self.log.close()

    def updateMeasurementLabels(self, measList):
        self.lastMeasured = measList
        for meas, label, zero in zip(measList, self.measResult_labels, self.zeros):
            label.setText(f"{meas-zero:.2f} mT")

    def setZero(self,n):
        self.zeros[n] = self.lastMeasured[n]

    def storeResult(self,n):
        currentDate = QDate.currentDate().toString()
        currentTime = QTime.currentTime().toString()
        self.log.write(f"{n}\t{currentDate}\t{currentTime}\t{(self.lastMeasured[n]-self.zeros[n]):.2f}\t{self.zeros[n]:.2f}\n")
        self.log.flush()
        
    def createLogFile(self):
        try:
            fileExists = False
            if os.path.isfile(self.filename.text()): # The file already exist
                fileExists = True
            self.log = open(self.filename.text(), "a")
            if not fileExists:
                self.log.write("Station N.\tDate\tTime\tB (mT)\tZero (mT)\n")
                self.log.flush()
            return [True, None]
        except Exception as e:
            return [False, str(e)]
    
if __name__ == '__main__':
    def run_app():
        # Create the Qt Application
        app = QApplication(sys.argv)
        # Create and show the form
        form = MainInterface()
        form.show()
        # Run the main Qt loop
        app.exec()
    run_app()