from PythonAtlasObj import *
from PythonSessionObj import *
from PythonParamObj import *
import time
import datetime
import pandas as pd
import numpy as np
import InfluxTools
import csv
from influxdb import InfluxDBClient
from influxdb import DataFrameClient

# Define required sampling frequency for import
fMaster = 100

# Set collection of files to be ingested
files_to_import = [r"C:\GIT\formulaebattery\DataAnalysis\Scripts\Python\Influx_testing\data\181215_110400_218_ADR_R_T01_BMW_TD1_0_23_27_1_6.ssn"]

# Set list of RESS parameters to import from ATLAS as timeseries (i.e. to become Influx fields)
params_to_import = [r'BMU_Stats_Pack_Curr:MCOREDBIOS',
                    r'BMU_Stats_Pack_Vbatt:MCOREDBIOS',
                    r'BMU_Debug_Pack_CTemp_Max:MCOREDBIOS',
                    r'BMU_Stats_Pack_Soc:MCOREDBIOS']

# Set list of RESS parameters to import as tags
tags_to_import = [r'BMU_Debug_Pack_SrlNum:MCOREDBIOS',
                  r'BMS_sw_micro:MCOREDBIOS',
                  'sTeamID']

# Set measurement label for influxDB
influx_measurement = 'FormulaE_Season5_Beta'

# Use DataFrameClient rather than InfluxDBClient directly to take advantage of using pandas DataFrames
# ==== Set-up InfluxDB connection
host = 'localhost'
port = 8086
user = 'root'
password = 'root'
dbname = 'RESS_data'
# dbuser = ''
# dbuser_password = ''
try:
    client = DataFrameClient(host, port, user, password, dbname)
except:
    print('Something went wrong with establishing the InfluxDB connection')

# Initiate ATLAS sessions
try:
    pyATLAS = PythonAtlasObj()
    pySession = PythonSessionObj(pyATLAS)
except:
    print('Something went wrong trying to open ATLAS 9.\n  '
          'Do you have a valid license?\n '
          'Try manually opening ATLAS 9 first')

# For each ATLAS session
for j in range(len(files_to_import)):

    # Load session into ATLAS
    try:
        print('Opening ' + str(files_to_import[j]) + ' into ATLAS')
        pySession.load_session(nlayer=1, sessionpath=files_to_import[j], show_slow_row=True)
    except:
        print("Could not load: " + str(files_to_import[j]) + "\n"
            "Check if this file exists. \n"
            "Do you have the correct consortium License: \"Atieva Battery\"?")


    # For each of the parameters selected (to become Influx fields)
    for i in range(len(params_to_import)):

        # Initialise DataFrame
        df_final = pd.DataFrame()



        try:
            # Get timeseries of that parameter from ATLAS
            # Returns list of tuples [0]: Data array [1]: Signal sampling frequency [2]: Time array
            param_temp = PythonParamObj(pySession, params_to_import[i]).getTimeSeries(opt="Time")
        except:
            print('There was a problem loading the parameter: ' + str(params_to_import[i]) +
                  '\nDoes this parameter exist in the specified session?'
                  '\nDo you have the correct PUL file for this session and does ATLAS point to it?')

        # Resize timeseries to required frequency
        if param_temp[1] != fMaster:
            # Super-sample
            if param_temp[1] < fMaster:
                param_temp_series = param_temp[0].repeat(fMaster/param_temp[1], axis=0)
            # Sub-sample
            else:
                param_temp_series = param_temp[0][0::(param_temp[1]/fMaster)]
        else:
            param_temp_series = param_temp[0]

        # Force length of first parameter to be the length of all subsequent parameters and determine the time vector
        if i == 0:
            lenMaster = len(param_temp_series)

            # Determine time vector - NOTE ATLAS export is nanoseconds into that day, so also need to combine with
            # unix epoch time for 00:00 of the date of the session.
            tStart = param_temp[2][0]
            tEnd = param_temp[2][-1]
            nStep = 1/fMaster
        # Linearly spaced time vector of nanosecondns into day
        tSeries = np.linspace(tStart, tEnd, lenMaster)

        # Get date of session from session data
        try:
            tDateSortable = PythonParamObj(pySession, r'tMCOREDSortableDate:MCORED').getStartVal()

        except:
            print('Could not find date parameter in that session, will not be ingested')

        # Convert sortable date of format YYMMDD into unix epoch time in nanoseconds
        dateUnix = time.mktime(datetime.datetime.strptime(str(int(tDateSortable)), "%y%m%d").timetuple())*1e9
        # Combine nanoseconds into day with unix time for that day
        tSeries = tSeries + dateUnix

        # Initiate DataFrame with the time vector, converting back to date-time
        # === NOTE: Datetime will be UTC
        df_final = pd.DataFrame(tSeries, columns=["Time"])
        df_final = pd.DataFrame(pd.to_datetime(df_final['Time'], unit='ns'))

        # Force all subsequent parameter series to be of the same length
        if len(param_temp_series) > lenMaster:
            # Remove last entries if this parameter happens to be longer than the first
            antiPadding = len(param_temp_series)-lenMaster
            param_temp_series = param_temp_series[:-antiPadding]

        elif len(param_temp_series) < lenMaster:
            # Pad with zeros where this parameter is not as long as the first
            padding = lenMaster - len(param_temp_series)
            param_temp_series = np.concatenate([param_temp_series, np.zeros(padding)])

        # Add this parameter to the DataFrame
        df_final[str(params_to_import[i])] = pd.Series(param_temp_series)

        # === Implement as a loop in the future
        # Extracts tags
        NBatterySerial = PythonParamObj(pySession, tags_to_import[0]).getStartVal()
        NBMSSwMicro = PythonParamObj(pySession, tags_to_import[1]).getStartVal()

        # ==== Force for now, but need conversion function from RESSDatabase project
        sTeamID = "AUD"

        df_final[str(tags_to_import[0])] = NBatterySerial
        df_final[str(tags_to_import[1])] = NBMSSwMicro
        df_final['sTeamID'] = sTeamID

        # Set the index of the DataFrame to be the time column
        df_final = df_final.set_index('Time')

        # Write to influxDB
        try:
            print('Writing ' + str(params_to_import[i]) + ' to InfluxDB')
            client.write_points(dataframe=df_final, measurement=influx_measurement,tag_columns=tags_to_import)
        except:
            print('Failed to write to influxDB')