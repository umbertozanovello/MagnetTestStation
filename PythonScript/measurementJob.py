from PyQt6.QtCore import QObject, pyqtSignal, QVariant

class MeasurementJob(QObject):

    measAvailable = pyqtSignal(QVariant)
    error = pyqtSignal(QVariant)

    def __init__(self, serialObj):
        super(MeasurementJob, self).__init__()
        self.stopMeasuring = False
        self.serialObj = serialObj

    def run(self):
        self.stopMeasuring = False
        while(not self.stopMeasuring):
            res = self.serialObj.startMeasure()
            if res[0]:
                self.measAvailable.emit(res[1])
