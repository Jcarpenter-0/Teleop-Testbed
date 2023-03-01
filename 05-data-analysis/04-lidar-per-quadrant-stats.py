import pandas as pd
import numpy as np

#dataDF = pd.read_csv('./data-analysis/lidar-dataset-multi-radio.csv')
dataDF = pd.read_csv('./data-analysis/lidar-dataset-single-radio.csv')


q1Count = 0
q1Losses = 0
q1Latencies = []

q2Count = 0
q2Losses = 0
q2Latencies = []

q3Count = 0
q3Losses = 0
q3Latencies = []

q4Count = 0
q4Losses = 0
q4Latencies = []


for rowIDX, row in dataDF.iterrows():

    azimuthAngle = row['azimuth_x']

    if azimuthAngle <= 45 or azimuthAngle >= 315:
        q1Count += 1
        if row['Latency'] == -1:
            q1Losses += 1
        else:
            q1Latencies.append(row['Latency'])
    elif azimuthAngle >= 45 and azimuthAngle <= 135:
        q2Count += 1
        if row['Latency'] == -1:
            q2Losses += 1
        else:
            q2Latencies.append(row['Latency'])

    elif azimuthAngle >= 135 and azimuthAngle <= 225:
        q3Count += 1
        if row['Latency'] == -1:
            q3Losses += 1
        else:
            q3Latencies.append(row['Latency'])

    elif azimuthAngle >= 225 and azimuthAngle <= 315:
        q4Count += 1
        if row['Latency'] == -1:
            q4Losses += 1
        else:
            q4Latencies.append(row['Latency'])




print('Q1 {}% {}+-{}'.format(q1Losses/q1Count, np.mean(q1Latencies), np.std(q1Latencies)))
print('Q2 {}% {}+-{}'.format(q1Losses/q2Count, np.mean(q2Latencies), np.std(q2Latencies)))
print('Q3 {}% {}+-{}'.format(q1Losses/q3Count, np.mean(q3Latencies), np.std(q3Latencies)))
print('Q4 {}% {}+-{}'.format(q1Losses/q4Count, np.mean(q4Latencies), np.std(q4Latencies)))