import numpy as np


class PythonParamObj:

    def __init__(self, pySessionObj=None, sSignal=r""):
        self.pySession = pySessionObj

        try:
            self.hParam = self.pySession.hParams.Item(sSignal)
            self.hPDA = self.pySession.hSession.CreateParamDataAccess(self.hParam)
            self.name = sSignal
            self.tStart = self.pySession.getStartTime()
            self.tEnd = self.pySession.getEndTime()
            self.NSamples = self.hPDA.GetSampleCount(self.tStart, self.tEnd)
            self.Data = self.hPDA.GetSamples(self.NSamples, self.tStart, self.tEnd)
            self.freq = self.hParam.MaxFrequency
        except:
            print(str(sSignal) + ' Does not exists in this session. Table will be populated with Null')
            self.hParam = None
            self.hPDA = None
            self.name = None
            self.tStart = None
            self.tEnd = None
            self.freq = None
            self.NSamples = None
            self.Data = None

    def getStartVal(self):
        if self.hParam is None:
            return 0
        else:

            condition = np.array(self.Data[2]) == 1
            npData = np.extract(condition, np.array(self.Data[1]))
            try:
                npData = npData[np.nonzero(npData)]
            except:
                npData = 0

            if len(npData) == 0:
                npData = 0
                return npData
            else:
                return npData[0].astype(np.float32)

    def getEndVal(self):
        if self.hParam is None:
            return 0
        else:

            condition = np.array(self.Data[2]) == 1
            npData = np.extract(condition, np.array(self.Data[1]))
            try:
                npData = npData[np.nonzero(npData)]
            except:
                npData = 0

            if len(npData) == 0:
                npData = 0
                return npData
            else:
                return npData[-1].astype(np.float32)

    def getMinMaxVal(self):
        if self.hParam is None:
            return 0, 0
        else:
            condition = np.array(self.Data[2]) == 1
            npData = np.extract(condition, np.array(self.Data[1]))
            try:
                npMax = np.amax(npData)
            except:
                npMax = np.zeros(1)

            try:
                npMin = np.amin(npData[np.nonzero(npData)])
            except:
                npMin = np.zeros(1)

            return npMax.astype(np.float32), npMin.astype(np.float32)

    def integrate(self, opt=None):
        """ Returns the integral of the specified session parameter. Defaults to two-sided integral, with option
            opt = "pos" for integral of positive values only or opt = "neg" for negative one-sided integral
            ("neg" still returns positive integral value)
        """
        if self.hParam is None:
            return 0
        else:

            if self.freq == 0:
                self.freq = 1  # If frequency is returned as 0, then parameter was likely to be logged in Row data at 1Hz
            period = 1 / self.freq

            condition = np.array(self.Data[2]) == 1
            npData = np.extract(condition, np.array(self.Data[1]))

            if opt == "pos":
                npData[npData < 0] = 0
                integral = np.trapz(npData, dx=period)

                return integral.astype(np.float32)

            elif opt == "neg":
                npData[npData > 0] = 0
                npData = npData*-1

                integral = np.trapz(npData, dx=period)
                return integral.astype(np.float32)
            else:
                integral = np.trapz(npData, dx=period)
                return integral.astype(np.float32)

    def timeInState(self, cond=0, opt='none'):
        """ Returns the time in seconds where value of signal matches cond
            Options 'none' = Return only time in that state
                    'sampleSet' = Return also the sample data of that parameter in that
                 """
        if self.hParam is None:
            return 0
        else:
            if self.freq == 0:
                self.freq = 1

            condition = np.array(self.Data[2]) == 1
            npData = np.extract(condition, np.array(self.Data[1]))

            condition = np.array(npData) == cond  # Drive
            npTime = np.extract(condition, np.array(self.Data[3]))
            tSession = npTime.size / self.freq

            return tSession

    # def cycleRMS(self, opt='drive'):
    #     """ Returns the RMS of the specified signal for the period when the BMS is in Drive state only
    #     Option 'moving' = condition where VCar > 1kph instead of Drive condition.
    #     """
    #
    #     if opt == 'drive':
    #
    #         # Make sure length is equal
    #         nDataLength = len(self.Data[1])
    #         driveMask = self.pySession.driveMask
    #
    #         if len(driveMask) >= nDataLength:
    #             driveMask = driveMask[:nDataLength]
    #         else:
    #             nPadding = nDataLength - len(driveMask)
    #             driveMask = np.concatenate([driveMask, np.zeros(nPadding)])
    #
    #         # Extract input signal only where condition is met
    #         npData = np.extract(driveMask, np.array(self.Data[1]))
    #
    #         rms = np.sqrt(np.mean(npData ** 2))
    #
    #         return rms
    #
    #     elif opt == 'moving':
    #
    #         nDataLength = len(self.Data[1])
    #         movingMask = self.pySession.movingMask
    #
    #         if len(movingMask) >= nDataLength:
    #             movingMask = movingMask[:nDataLength]
    #         else:
    #             nPadding = nDataLength - len(movingMask)
    #             movingMask = np.concatenate([movingMask, np.zeros(nPadding)])
    #
    #         # Extract input signal only where condition is met
    #         npData = np.extract(movingMask, np.array(self.Data[1]))
    #
    #         rms = np.sqrt(np.mean(npData ** 2))
    #
    #         return rms



    def getTimeSeries(self, opt='None'):
        """ Returns complete timeseries data along with sample frequency
        option to also return ATLAS time vector"""

        if self.hParam is None:
            return 0

        if self.freq == 0:
            self.freq = 1

        condition = np.array(self.Data[2]) == 1
        npData = np.extract(condition, np.array(self.Data[1]))

        if opt == 'None':
            return npData, self.freq

        elif opt == 'Time':
            npDataTime = np.extract(condition, np.array(self.Data[3]))

            return npData, self.freq, npDataTime

    # def getTimeSeries2(self):
    #     """ Returns complete timeseries data along with sample frequency """
    #     tStart = self.pySession.hSession.StartTime
    #     tEnd = self.pySession.hSession.EndTime
    #     NSamples = self.hPDA.GetSampleCount(tStart, tEnd)
    #     Data = self.hPDA.GetSamples(NSamples, tStart, tEnd)
    #
    #     return Data

    def getAverage(self, opt='none', opt2='none'):
        """ Return the average value of a timeseries, options to average only give a certain condition
        opt = 'moving':  Provide average of signal only when vehicle speed > 1kph
        opt = 'drive': Provide average of signal when BMS is in Drive State
        opt2 = 'rms' for RMS average.  """
        if self.hParam is None:
            return 0

        condition = np.array(self.Data[2]) == 1
        npData = np.extract(condition, np.array(self.Data[1]))

        if opt == 'none':
            if opt2 == 'none':
                DataAvg = np.mean(npData)
            else:
                DataAvg = np.sqrt(np.mean(npData) ** 2)

            return DataAvg

        elif opt == 'moving':


            movingMask = self.pySession.getMovingMask()

            Data = np.array(npData).repeat(100/self.freq, axis=0)
            nDataLength = len(Data)
            if len(movingMask) >= nDataLength:
                movingMask = movingMask[:nDataLength]
            else:
                nPadding = nDataLength - len(movingMask)
                movingMask = np.concatenate([movingMask, np.zeros(nPadding)])

            # Extract input signal only where condition is met
            npData = np.extract(movingMask, np.array(Data))

            if opt2 == 'none':
                DataAvg = np.mean(npData)
            else:
                DataAvg = np.sqrt(np.mean(npData ** 2))

            return DataAvg

        elif opt == 'drive':

            nDataLength = len(npData)
            driveMask = self.pySession.getMovingMask()[1]

            if len(driveMask) >= nDataLength:
                driveMask = driveMask[:nDataLength]
            else:
                nPadding = nDataLength - len(driveMask)
                driveMask = np.concatenate([driveMask, np.zeros(nPadding)])

            # Extract input signal only where condition is met
            npData = np.extract(driveMask, np.array(npData))

            if opt2 == 'none':
                DataAvg = np.mean(npData)
            else:
                DataAvg = np.sqrt(np.mean(npData ** 2))

            return DataAvg

    def setInterval(self, tStart, tEnd):
        self.tStart = tStart
        self.tEnd = tEnd
        self.NSamples = self.hPDA.GetSampleCount(self.tStart, self.tEnd)
        self.Data = self.hPDA.GetSamples(self.NSamples, self.tStart, self.tEnd)

        return