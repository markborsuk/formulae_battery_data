import math
from pathlib import Path
from PythonParamObj import *

class PythonSessionObj:

    def __init__(self, pyAtlasObj=None):
        self.pyATLAS = pyAtlasObj
        self.NLayer = 0
        self.hLayer = None
        self.hSession = None
        self.hParams = None
        self.hLaps = None

    def load_session(self, nlayer, sessionpath=r"", show_slow_row=False):
        """
        Loads a session into a layer, replacing the session that was previously loaded in that layer

        Params:
            > nlayer -- Index of the Layer that the session will be loaded into. Long Integer
            > sessionpath -- Full path of the session to load.  String.

        Example:
            LoadSession( 3, "c:/MySessionFolder/12345_superTest.ssn")
        """
        #
        self.NLayer = nlayer-1

        # Load session into ATLAS
        self.pyATLAS.hATLAS.LoadSession(self.NLayer, sessionpath)

        self.hLayer = self.pyATLAS.hLayers.Item(self.NLayer)  # Returns the object in layer 1 (0 base)
        self.hSession = self.hLayer.Session
        self.hParams = self.hSession.Parameters
        self.hLaps = self.hSession.Laps
        self.tStart = self.hSession.StartTime
        self.tEnd = self.hSession.EndTime

        return

    def load_multi_session(self, nlayer, sessionpath=r""):
        """
        Loads a session into a layer, replacing the session that was previously loaded in that layer

        Params:
            > nlayer -- Index of the Layer that the session will be loaded into. Long Integer
            > sessionpath -- Full path of the session to load.  String.

        Example:
            LoadSession( 3, "c:/MySessionFolder/12345_superTest.ssn")
        """
        #
        self.NLayer = nlayer-1

        # Load session into ATLAS
        self.pyATLAS.hATLAS.LoadSession(self.NLayer, sessionpath)

        self.hLayer = self.pyATLAS.hLayers.Item(self.NLayer)  # Returns the object in layer 1 (0 base)
        self.hSession = self.hLayer.Session
        self.hParams = self.hSession.Parameters
        self.hLaps = self.hSession.Laps
        self.tStart = self.hSession.StartTime
        self.tEnd = self.hSession.EndTime

        return

    def getStartTime(self):
        """
        Returns the start time from current session
        """
        time = self.hSession.StartTime

        return time

    def getEndTime(self):
        """
        Returns the end time from current session
        """
        time = self.hSession.EndTime

        return time

    # def getStateMasks(self):
    #     pyNBMSState = PythonParamObj(self, r'BMU_Status_State_Main:MCOREDBIOS')
    #     NBMSState = pyNBMSState.getTimeSeries()[0]
    #
    #     driveMask = NBMSState == 2
    #     chargeMask = NBMSState == 1
    #     standbyMask = NBMSState == 3
    #     powerdownMask = NBMSState == 6
    #     faultMask = NBMSState == 4
    #
    #     return chargeMask,driveMask, standbyMask, faultMask,powerdownMask

    def getStateMasks(self, mask='drive', length=0):

        pyNBMSState = PythonParamObj(self, r'BMU_Status_State_Main:MCOREDBIOS')
        NBMSState = pyNBMSState.getTimeSeries()[0]

        initMask = NBMSState == 0
        driveMask = NBMSState == 2
        chargeMask = NBMSState == 1
        standbyMask = NBMSState == 3
        powerdownMask = NBMSState == 6
        faultMask = NBMSState == 4

        if len == 0:
            if mask =='charge':
                return chargeMask
            elif mask =='drive':
                return driveMask
            elif mask =='init':
                return initMask
            elif mask == 'standby':
                return standbyMask
            elif mask == 'fault':
                return faultMask
            elif mask == 'powerdown':
                return powerdownMask
            else:
                print('Mask ' + str(mask) + ' does not exist')

        else:
            scale = math.ceil(len(NBMSState) / length)
            if mask == 'charge':
                chargeMask = chargeMask[::scale]
                nPadding = length - len(chargeMask)
                chargeMask = np.concatenate([chargeMask, np.zeros(nPadding)])
                return chargeMask.astype(bool)

            elif mask == 'drive':
                driveMask = driveMask[::scale]
                nPadding = length - len(driveMask)
                driveMask = np.concatenate([driveMask, np.zeros(nPadding)])
                return driveMask.astype(bool)

            elif mask == 'init':
                initMask = initMask[::scale]
                nPadding = length - len(initMask)
                initMask = np.concatenate([initMask, np.zeros(nPadding)])
                return initMask.astype(bool)

            elif mask == 'standby':
                standbyMask = standbyMask[::scale]
                nPadding = length - len(standbyMask)
                standbyMask = np.concatenate([standbyMask, np.zeros(nPadding)])
                return standbyMask.astype(bool)

            elif mask == 'powerdown':
                powerdownMask = powerdownMask[::scale]
                nPadding = length - len(powerdownMask)
                powerdownMask = np.concatenate([powerdownMask, np.zeros(nPadding)])
                return powerdownMask.astype(bool)

            elif mask == 'fault':
                faultMask = faultMask[::scale]
                nPadding = length - len(faultMask)
                faultMask = np.concatenate([faultMask, np.zeros(nPadding)])
                return faultMask.astype(bool)

    def getMovingMask(self):
        pyVCar = PythonParamObj(self, r'ECU_BMU_Veh_Speed:MCOREDBIOS')
        VCar = pyVCar.getTimeSeries()[0]
        VCar = np.array(VCar.repeat(10, axis=0))
        movingMask = VCar > 1

        return movingMask


    def getSortableTime(self, t):
        """ Convert time in nanoseconds into a sortable timestamp in the format HHMMSS"""
        tSeconds = t*1e-9
        tMinutes = math.floor(tSeconds/60)
        tHours = math.floor(tMinutes/60)

        tMinutesRemain = math.trunc(tMinutes-tHours*60)
        tSecondsRemain = math.trunc(tSeconds-tMinutesRemain*60-tHours*60*60)

        tSortable = str(tHours).zfill(2) + str(tMinutesRemain).zfill(2) + str(tSecondsRemain).zfill(2)

        return tSortable

    def getParamList(self):
        """ Return a list of available parameters in session"""
        nCount = self.hParams.Count
        self.hParams.ShowSlowRowParameters()

        paramList = []

        for i in range(int(nCount)):
            hParam = self.hParams.Index(i)
            paramList.append(hParam.Name)

        return paramList

    def save_session_as(self, fileName):
        my_file = Path(fileName)
        if my_file.is_file():
            print("This file already exits in MASTER, session not saved")
            return
        else:
            self.hLayer.Session.SaveSessionAs(fileName)

    def close_session(self):
        self.hSession.Close()
        self.pyATLAS.hATLAS.CloseSession(self.NLayer)

    def sessionQuality(self):
        pyNBMSUptime = PythonParamObj(self, r'BMU_Status_State_Main:MCOREDBIOS')
        NSamplesValid = sum(np.array(pyNBMSUptime.Data[2]) == 1)
        rSessionQuality = NSamplesValid / pyNBMSUptime.NSamples

        return rSessionQuality, pyNBMSUptime.NSamples

    def getLapCount(self):
        nLap = self.hLaps.Count

        return nLap

    def getLapStartTime(self, NLap):
        tLapStart = self.hLaps.Item(NLap).StartTime
        return tLapStart

    def getLapEndTime(self, NLap):
        tLapEnd = self.hLaps.Item(NLap).EndTime
        return tLapEnd