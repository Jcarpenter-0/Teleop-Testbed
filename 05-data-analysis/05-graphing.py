import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# ========================================================

testsDF = pd.read_csv('../../../Analysis/tests.csv')
sensordataDF = pd.read_csv('../../../Analysis/sensor-results.csv')
cameradataDF = pd.read_csv('../../../Analysis/camera-results.csv')
TargetDirectory = '../../../Analysis/Figures/'


# ========================================================
CameraLabels = ['camera-1','camera-2','camera-3','camera-4']
SensorPorts = ['2379','2380','2381','8319','8320','8321','4000','4001','4002','4003','4004','4005']


OperatorLabel = 'net.interface.cellular[].homeoperator'
TechnologyLabel = 'net.interface.cellular[].technology.current'
RatLabel = 'net.interface.cellular[].rat'
BandLabel = 'net.interface.cellular[].band'
SensorLabel = 'Sensor-ID'
TestLabel = 'Test-ID'

CameraInterFrameLabel = 'Inter-Frame-Times (s)'
CameraFrameSizeLabel = 'Frame-Sizes (Bits)'

SensorIODLabel = 'Epoch-Receive-Timestamp-Difs'
SensorINDLabel = 'Send-Receive-Timings (Seconds)'
SensorTputLabel = 'Length-Of-Chunk-Received(Bytes)'

individualCameraTests = testsDF[(testsDF['Number-Of-Cameras'] == 1) & (testsDF['Actual-Test-Duration (seconds)'] >= 280)]['TestID'].values
IndividualLiDARTests = testsDF[((testsDF['Number-Of-LiDARs'] == 1) | (testsDF['Number-Of-Other-Sensors'] == 1)) & (testsDF['Actual-Test-Duration (seconds)'] >= 280)]['TestID'].values
#IndividualMiscTests = testsDF[(testsDF['Number-Of-Other-Sensors'] == 1) & (testsDF['Actual-Test-Duration (seconds)'] >= 280)]['TestID'].values
groupCameraTests = testsDF[(testsDF['Number-Of-Cameras'] == 4) & (testsDF['Number-Of-LiDARs'] == 0) & (testsDF['Number-Of-Other-Sensors'] == 0) & (testsDF['Actual-Test-Duration (seconds)'] >= 280)]['TestID'].values
groupLiDARTests = testsDF[((testsDF['Number-Of-LiDARs'] == 3) | (testsDF['Number-Of-Other-Sensors'] == 6)) & (testsDF['Actual-Test-Duration (seconds)'] >= 280)]['TestID'].values
#groupMiscTests = testsDF[(testsDF['Number-Of-Cameras'] == 0) & (testsDF['Number-Of-LiDARs'] == 0) & (testsDF['Number-Of-Other-Sensors'] == 6) & (testsDF['Actual-Test-Duration (seconds)'] >= 280)]['TestID'].values

fullTests = testsDF[(testsDF['Number-Of-Cameras'] == 4) & (testsDF['Number-Of-LiDARs'] == 3) & (testsDF['Number-Of-Other-Sensors'] == 6) & (testsDF['Actual-Test-Duration (seconds)'] >= 280)]['TestID'].values

# ========================================================
# Graph Carriers performance
if True:

    for cameraLabel in CameraLabels:

        testSubsets:pd.DataFrame = cameradataDF.loc[cameradataDF['Test-ID'].isin(individualCameraTests)]
        testSubsets = testSubsets[testSubsets[SensorLabel] == cameraLabel]

        if len(testSubsets) > 0:
            testSubsets.boxplot(column=[CameraInterFrameLabel],by=[OperatorLabel],figsize=(5,6), showfliers=False)
            plt.tight_layout()
            plt.savefig('{}boxplot-IOD-by-Operator-cond-single-{}.png'.format(TargetDirectory,cameraLabel))
            plt.close()

            testSubsets.boxplot(column=[CameraFrameSizeLabel],by=[OperatorLabel],figsize=(5,6), showfliers=False)
            plt.tight_layout()
            plt.savefig('{}boxplot-Framesize-by-Operator-cond-single-{}.png'.format(TargetDirectory,cameraLabel))
            plt.close()

            # Grouped Results
            testSubsets:pd.DataFrame = cameradataDF.loc[cameradataDF['Test-ID'].isin(groupCameraTests)]
            testSubsets = testSubsets[testSubsets[SensorLabel] == 'camera-1']
            testSubsets.boxplot(column=[CameraInterFrameLabel],by=[OperatorLabel], figsize=(5,6), showfliers=False)
            plt.tight_layout()
            plt.savefig('{}boxplot-IOD-by-Operator-cond-groups-{}.png'.format(TargetDirectory,cameraLabel))
            plt.close()

            testSubsets.boxplot(column=[CameraFrameSizeLabel],by=[OperatorLabel], figsize=(5,6), showfliers=False)
            plt.tight_layout()
            plt.savefig('{}boxplot-Framesize-by-Operator-cond-groups-{}.png'.format(TargetDirectory,cameraLabel))
            plt.close()

# ======================================================
# Sensor Results

if True:

    for sensorPort in SensorPorts:
        print('Graphing {}'.format(sensorPort))
        # Graph the IND by carrier
        testSubsets:pd.DataFrame = sensordataDF.loc[sensordataDF['Test-ID'].isin(IndividualLiDARTests)]
        # Filter out the "negative times" that resulted from microsecond rounding errors
        testSubsets = testSubsets[(testSubsets[SensorLabel] == int(sensorPort))]
        #testSubsets = testSubsets[testSubsets[SensorINDLabel] > 0]
        #testSubsets = testSubsets[testSubsets[SensorIODLabel] > 0]

        if len(testSubsets) > 0:
            uniqueTestsIds = testSubsets[TestLabel].unique()

            # Calculate the loss rates: packets and "observations"

            packetLossesPerTest = []
            observationLossesPerTest = []

            for sensorTestID in uniqueTestsIds:
                specificTest = testSubsets[testSubsets[TestLabel] == sensorTestID]

                sizeBeforeDropNa = len(specificTest)
                specificTestSentPackets = specificTest.dropna(subset=['Epoch-Receive-Timestamp'])
                specificTestLostPackets = specificTest[specificTest['Epoch-Receive-Timestamp'].isna()]

                print('Lost Packets {} {} {}'.format(sensorPort, sizeBeforeDropNa, len(specificTestLostPackets)/sizeBeforeDropNa))



            testSubsets.boxplot(column=[SensorIODLabel], by=[OperatorLabel], figsize=(5, 6), showfliers=False)
            plt.tight_layout()
            plt.savefig('{}boxplot-IOD-by-Operator-cond-single-{}-by-carrier.png'.format(TargetDirectory, sensorPort))
            plt.close()

            testSubsets.boxplot(column=[SensorINDLabel], by=[OperatorLabel], figsize=(5, 6), showfliers=False)
            plt.tight_layout()
            plt.savefig('{}boxplot-IND-by-Operator-cond-single-{}-by-carrier.png'.format(TargetDirectory, sensorPort))
            plt.close()

        testSubsets: pd.DataFrame = sensordataDF.loc[sensordataDF['Test-ID'].isin(groupLiDARTests)]
        testSubsets = testSubsets[(testSubsets[SensorLabel] == int(sensorPort))]
        #testSubsets = testSubsets[testSubsets[SensorINDLabel] > 0]
        #testSubsets = testSubsets[testSubsets[SensorIODLabel] > 0]

        if len(testSubsets) > 0:
            print('Groups')
            uniqueTestsIds = testSubsets[TestLabel].unique()

            for sensorTestID in uniqueTestsIds:

                specificTest = testSubsets[testSubsets[TestLabel] == sensorTestID]

                sizeBeforeDropNa = len(specificTest)
                specificTestSentPackets = specificTest.dropna(subset=['Epoch-Receive-Timestamp'])
                specificTestLostPackets = specificTest[specificTest['Epoch-Receive-Timestamp'].isna()]

                print('Lost Packets {} {} {}'.format(sensorPort, sizeBeforeDropNa, len(specificTestLostPackets)/sizeBeforeDropNa))

            testSubsets.boxplot(column=[SensorIODLabel], by=[OperatorLabel], figsize=(5, 6), showfliers=False)
            plt.tight_layout()
            plt.savefig('{}boxplot-IOD-by-Operator-cond-group-{}-by-carrier.png'.format(TargetDirectory, sensorPort))
            plt.close()

            testSubsets.boxplot(column=[SensorINDLabel], by=[OperatorLabel], figsize=(5, 6), showfliers=False)
            plt.tight_layout()
            plt.savefig('{}boxplot-IND-by-Operator-cond-group-{}-by-carrier.png'.format(TargetDirectory, sensorPort))
            plt.close()