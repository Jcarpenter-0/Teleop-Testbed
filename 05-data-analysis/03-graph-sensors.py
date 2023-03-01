import glob
import pandas as pd
import matplotlib.pyplot as plt
import re
import seaborn as sns
import os
import numpy as np
from datetime import datetime
import matplotlib.gridspec as gridspec
from prettytable import PrettyTable
import matplotlib.patches as patches
from brokenaxes import brokenaxes
import matplotlib.gridspec as GridSpec
import matplotlib.colors


# ========================================================
Tests = glob.glob('../../../Analysis/*-Datasets-*/')
TestsDataDF = pd.read_csv('../../../Analysis/tests.csv')
TmpDirectory = '../../../Datasets/tmp/'
AnalysisDir = '../../../Analysis/'

# ========================================================
#CameraDataDF = pd.read_csv(AnalysisDir + 'camera-results.csv')
#CameraDataDF = CameraDataDF.dropna(subset=['Frame-Time-With-First-Frame-Delay(s)'])
#CameraDataDF = CameraDataDF.fillna(method='pad')


#LiDARDataDF = pd.read_csv(AnalysisDir + 'sensor-results.csv')
#LiDARDataDF = LiDARDataDF.dropna(subset=['Receive-Timestamp(s)'])
#LiDARDataDF = LiDARDataDF.fillna(method='pad')

SensorDataDF = pd.read_csv(AnalysisDir + 'macro-tcp-sensor-rtt-data.csv')

# ========================================================
# Graphing the Camera

# Plot Timing over single trace
if False:
    QoESampleDF = pd.DataFrame()

    QoESampleDF['Verizon'] = CameraDataDF[(CameraDataDF['net.interface.cellular[].homeoperator'].str.contains('Verizon')) &
                                          (CameraDataDF['Sensor-ID'] == 'camera-1') &
                                          (CameraDataDF['Test-ID'] == 87)].reset_index().iloc[:7000]['Frame-Time-With-First-Frame-Delay(s)']
    QoESampleDF['T-Mobile'] = CameraDataDF[(CameraDataDF['net.interface.cellular[].homeoperator'].str.contains('T-Mobile')) &
                                          (CameraDataDF['Sensor-ID'] == 'camera-1') &
                                          (CameraDataDF['Test-ID'] == 43)].reset_index().iloc[:7000]['Frame-Time-With-First-Frame-Delay(s)']
#    QoESampleDF['AT&T'] = CameraDataDF[(CameraDataDF['net.interface.cellular[].homeoperator'].str.contains('AT&T')) &
#                                          (CameraDataDF['Sensor-ID'] == 'camera-1') &
#                                          (CameraDataDF['Test-ID'] == 63)].reset_index().iloc[:7000]['Frame-Time-With-First-Frame-Delay(s)']


    fig = plt.figure(figsize=(5, 4))
    gs1 = gridspec.GridSpec(1, 1, wspace=0.2, hspace=0.08, top=.94, bottom=0.23, left=0.2, right=0.99, figure=fig)
    ax0 = plt.subplot(gs1[0])
    ax0.set_ylabel('Frame Delay (s)', fontsize=12)
    ax0.set_ylim(0, 2.5)
    ax0.set_yticks([i for i in np.arange(0, 2.5, 0.2)])
    ax0.set_xlabel('Frame Number', fontsize=13)
    sns.lineplot(QoESampleDF,ax=ax0)

    trans = ax0.get_xaxis_transform()
    ax0.text(0.12, 0.12, 'Ideal', color='#800000', fontweight='bold')
    ax0.annotate("", xy=(0.1, 0.07), xycoords=trans,
                      xytext=(7000.5, 0.07), fontsize=12, color='#800000', weight='bold',
                      va="center", ha="center",
                      bbox=dict(boxstyle="round", fc="w", alpha=0),
                 arrowprops=dict(arrowstyle="-", color='#800000', lw=1.4))

    plt.show()
    plt.close(fig)


if False:

    QoEMacroDF = pd.DataFrame()
    QoEMacroDF['Verizon'] = CameraDataDF[(CameraDataDF['net.interface.cellular[].homeoperator'].str.contains('Verizon')) &
                                          (CameraDataDF['Sensor-ID'] == 'camera-1') &
                                          (CameraDataDF['Test-ID'].isin([87, 86]))].reset_index()['Frame-Time-With-First-Frame-Delay(s)']
    QoEMacroDF['T-Mobile'] = CameraDataDF[(CameraDataDF['net.interface.cellular[].homeoperator'].str.contains('T-Mobile')) &
                                          (CameraDataDF['Sensor-ID'] == 'camera-1') &
                                          (CameraDataDF['Test-ID'].isin([43,44,45]))].reset_index()['Frame-Time-With-First-Frame-Delay(s)']
#    QoEMacroDF['AT&T'] = CameraDataDF[(CameraDataDF['net.interface.cellular[].homeoperator'].str.contains('AT&T')) &
#                                          (CameraDataDF['Sensor-ID'] == 'camera-1') &
#                                          (CameraDataDF['Test-ID'].isin([64,63]))].reset_index()['Frame-Time-With-First-Frame-Delay(s)']

    fig = plt.figure(figsize=(5, 4))
    gs1 = gridspec.GridSpec(1, 1, wspace=0.2, hspace=0.08, top=.94, bottom=0.23, left=0.2, right=0.99, figure=fig)
    ax0 = plt.subplot(gs1[0])
    ax0.set_ylim(0, 2.5)
    ax0.set_yticks([i for i in np.arange(0, 2.5, 0.2)])
    ax0.set_ylabel('Frame Delay (s)', fontsize=12)

    #ax0.set_xlabel('Frame Number', fontsize=13)

    trans = ax0.get_xaxis_transform()
    ax0.text(0.12, 0.12, 'Ideal', color='#800000', fontweight='bold')
    ax0.annotate("", xy=(-0.4, 0.07), xycoords=trans,
                      xytext=(2.5, 0.07), fontsize=12, color='#800000', weight='bold',
                      va="center", ha="center",
                      bbox=dict(boxstyle="round", fc="w", alpha=0),
                 arrowprops=dict(arrowstyle="-", color='#800000', lw=1.4))

    sns.boxplot(QoEMacroDF,ax=ax0)

    plt.show()
    plt.close(fig)

# ==============================

if False:

    QoEMacroGroupsDF = pd.DataFrame()
    QoEMacroGroupsDF['Verizon'] = CameraDataDF[(CameraDataDF['net.interface.cellular[].homeoperator'].str.contains('Verizon')) &
                                          (CameraDataDF['Sensor-ID'] == 'camera-1') &
                                          (CameraDataDF['Test-ID'].isin([21, 22]))].reset_index()['Frame-Time-With-First-Frame-Delay(s)']
    QoEMacroGroupsDF['T-Mobile'] = CameraDataDF[(CameraDataDF['net.interface.cellular[].homeoperator'].str.contains('T-Mobile')) &
                                          (CameraDataDF['Sensor-ID'] == 'camera-1') &
                                          (CameraDataDF['Test-ID'].isin([4,5,13,14]))].reset_index()['Frame-Time-With-First-Frame-Delay(s)']

    fig = plt.figure(figsize=(5, 4))
    gs1 = gridspec.GridSpec(1, 1, wspace=0.2, hspace=0.08, top=.94, bottom=0.23, left=0.2, right=0.99, figure=fig)
    ax0 = plt.subplot(gs1[0])
    ax0.set_yticks([i for i in np.arange(0, 0.5, 0.05)])
    ax0.set_ylabel('Frame Delay (s)', fontsize=12)

    #ax0.set_xlabel('Frame Number', fontsize=13)

    trans = ax0.get_xaxis_transform()
    ax0.text(0.12, 0.12, 'Ideal', color='#800000', fontweight='bold')
    ax0.annotate("", xy=(-0.4, 0.15), xycoords=trans,
                      xytext=(2.5, 0.15), fontsize=12, color='#800000', weight='bold',
                      va="center", ha="center",
                      bbox=dict(boxstyle="round", fc="w", alpha=0),
                 arrowprops=dict(arrowstyle="-", color='#800000', lw=1.4))

    sns.boxplot(QoEMacroGroupsDF,ax=ax0, showfliers=False)

    plt.show()
    plt.close(fig)

# ================================
# Graphing camera-4

if False:

    QoEMacroDF = pd.DataFrame()
    QoEMacroDF['Verizon'] = CameraDataDF[(CameraDataDF['net.interface.cellular[].homeoperator'].str.contains('Verizon')) &
                                          (CameraDataDF['Sensor-ID'] == 'camera-4') &
                                          (CameraDataDF['Test-ID'].isin([69, 70]))].reset_index()['Frame-Time-With-First-Frame-Delay(s)']
    QoEMacroDF['T-Mobile'] = CameraDataDF[(CameraDataDF['net.interface.cellular[].homeoperator'].str.contains('T-Mobile')) &
                                          (CameraDataDF['Sensor-ID'] == 'camera-4') &
                                          (CameraDataDF['Test-ID'].isin([39,40]))].reset_index()['Frame-Time-With-First-Frame-Delay(s)']
    #QoEMacroDF['AT&T'] = CameraDataDF[(CameraDataDF['net.interface.cellular[].homeoperator'].str.contains('AT&T')) &
    #                                      (CameraDataDF['Sensor-ID'] == 'camera-4') &
    #                                      (CameraDataDF['Test-ID'].isin([61,62]))].reset_index()['Frame-Time-With-First-Frame-Delay(s)']

    fig = plt.figure(figsize=(5, 4))
    gs1 = gridspec.GridSpec(1, 1, wspace=0.2, hspace=0.08, top=.94, bottom=0.23, left=0.2, right=0.99, figure=fig)
    ax0 = plt.subplot(gs1[0])
    ax0.set_yticks([i for i in np.arange(0, 2.7, 0.2)])
    ax0.set_ylabel('Frame Delay (s)', fontsize=12)

    #ax0.set_xlabel('Frame Number', fontsize=13)

    trans = ax0.get_xaxis_transform()
    ax0.text(0.12, 0.12, 'Ideal', color='#800000', fontweight='bold')
    ax0.annotate("", xy=(-0.4, 0.07), xycoords=trans,
                      xytext=(2.5, 0.07), fontsize=12, color='#800000', weight='bold',
                      va="center", ha="center",
                      bbox=dict(boxstyle="round", fc="w", alpha=0),
                 arrowprops=dict(arrowstyle="-", color='#800000', lw=1.4))

    sns.boxplot(QoEMacroDF,ax=ax0)

    plt.show()
    plt.close(fig)


if False:

    # (CameraDataDF['Frame-Time-With-First-Frame-Delay(s)'] > 0)

    QoEMacroGroupsDF = pd.DataFrame()
    QoEMacroGroupsDF['Verizon'] = CameraDataDF[(CameraDataDF['net.interface.cellular[].homeoperator'].str.contains('Verizon')) &
                                          (CameraDataDF['Sensor-ID'] == 'camera-4') &
                                          (CameraDataDF['Test-ID'].isin([21]))].reset_index()['Frame-Time-With-First-Frame-Delay(s)']
    QoEMacroGroupsDF['T-Mobile'] = CameraDataDF[(CameraDataDF['net.interface.cellular[].homeoperator'].str.contains('T-Mobile')) &
                                          (CameraDataDF['Sensor-ID'] == 'camera-4') &
                                          (CameraDataDF['Test-ID'].isin([4,5]))].reset_index()['Frame-Time-With-First-Frame-Delay(s)']

    fig = plt.figure(figsize=(5, 4))
    gs1 = gridspec.GridSpec(1, 1, wspace=0.2, hspace=0.08, top=.94, bottom=0.23, left=0.2, right=0.99, figure=fig)
    ax0 = plt.subplot(gs1[0])
    ax0.set_ylim(0, 2.5)
    ax0.set_yticks([i for i in np.arange(0, 2.5, 0.2)])
    ax0.set_ylabel('Frame Delay (s)', fontsize=12)

    #ax0.set_xlabel('Frame Number', fontsize=13)

    trans = ax0.get_xaxis_transform()
    ax0.text(0.12, 0.12, 'Ideal', color='#800000', fontweight='bold')
    ax0.annotate("", xy=(-0.4, 0.04), xycoords=trans,
                      xytext=(2.5, 0.04), fontsize=12, color='#800000', weight='bold',
                      va="center", ha="center",
                      bbox=dict(boxstyle="round", fc="w", alpha=0),
                 arrowprops=dict(arrowstyle="-", color='#800000', lw=1.4))

    sns.boxplot(QoEMacroGroupsDF,ax=ax0, showfliers=False)

    plt.show()
    plt.close(fig)

# ========================================================
# Graphing the LiDARs

# ========================================================
if False:
    QoESampleDF = pd.DataFrame()

    QoESampleDF['Verizon'] = LiDARDataDF[(LiDARDataDF['net.interface.cellular[].homeoperator'].str.contains('Verizon')) &
                                          (LiDARDataDF['Sensor-ID'] == 2379) &
                                          (LiDARDataDF['Test-ID'] == 85)].reset_index().iloc[:3000]['Send-Receive-Timings (Seconds)']
    QoESampleDF['T-Mobile'] = LiDARDataDF[(LiDARDataDF['net.interface.cellular[].homeoperator'].str.contains('T-Mobile')) &
                                          (LiDARDataDF['Sensor-ID'] == 2379) &
                                          (LiDARDataDF['Test-ID'] == 38)].reset_index().iloc[:3000]['Send-Receive-Timings (Seconds)']
#    QoESampleDF['AT&T'] = LiDARDataDF[(LiDARDataDF['net.interface.cellular[].homeoperator'].str.contains('AT&T')) &
#                                          (LiDARDataDF['Sensor-ID'] == 2379) &
#                                          (LiDARDataDF['Test-ID'] == 60)].reset_index().iloc[:3000]['Send-Receive-Timings (Seconds)']


    fig = plt.figure(figsize=(5, 4))
    gs1 = gridspec.GridSpec(1, 1, wspace=0.2, hspace=0.08, top=.94, bottom=0.23, left=0.2, right=0.99, figure=fig)
    ax0 = plt.subplot(gs1[0])
    ax0.set_ylabel('Packet Delay (Seconds)', fontsize=12)
    ax0.set_ylim(0, 2.5)
    ax0.set_yticks([i for i in np.arange(0, 2.5, 0.2)])
    ax0.set_xlabel('Packet Number', fontsize=13)
    sns.lineplot(QoESampleDF,ax=ax0)

    trans = ax0.get_xaxis_transform()
    ax0.text(0.12, 0.12, 'Ideal', color='#800000', fontweight='bold')
    ax0.annotate("", xy=(0.1, 0.04), xycoords=trans,
                      xytext=(7000.5, 0.04), fontsize=12, color='#800000', weight='bold',
                      va="center", ha="center",
                      bbox=dict(boxstyle="round", fc="w", alpha=0),
                 arrowprops=dict(arrowstyle="-", color='#800000', lw=1.4))

    plt.show()
    plt.close(fig)


if False:

    QoEMacroDF = pd.DataFrame()
    QoEMacroDF['Verizon'] = LiDARDataDF[(LiDARDataDF['net.interface.cellular[].homeoperator'].str.contains('Verizon')) &
                                          (LiDARDataDF['Sensor-ID'] == 2379) &
                                          (LiDARDataDF['Test-ID'].isin([85, 84]))].reset_index()['Send-Receive-Timings (Seconds)']
    QoEMacroDF['T-Mobile'] = LiDARDataDF[(LiDARDataDF['net.interface.cellular[].homeoperator'].str.contains('T-Mobile')) &
                                          (LiDARDataDF['Sensor-ID'] == 2379) &
                                          (LiDARDataDF['Test-ID'].isin([38,37]))].reset_index()['Send-Receive-Timings (Seconds)']
    #QoEMacroDF['AT&T'] = CameraDataDF[(CameraDataDF['net.interface.cellular[].homeoperator'].str.contains('AT&T')) &
    #                                      (CameraDataDF['Sensor-ID'] == 'camera-4') &
    #                                      (CameraDataDF['Test-ID'].isin([61,62]))].reset_index()['Frame-Time-With-First-Frame-Delay(s)']

    fig = plt.figure(figsize=(5, 4))
    gs1 = gridspec.GridSpec(1, 1, wspace=0.2, hspace=0.08, top=.94, bottom=0.23, left=0.2, right=0.99, figure=fig)
    ax0 = plt.subplot(gs1[0])
    ax0.set_ylim(0, 2.5)
    ax0.set_yticks([i for i in np.arange(0, 2.5, 0.2)])
    ax0.set_ylabel('Frame Delay (s)', fontsize=12)

    #ax0.set_xlabel('Frame Number', fontsize=13)

    trans = ax0.get_xaxis_transform()
    ax0.text(0.12, 0.12, 'Ideal', color='#800000', fontweight='bold')
    ax0.annotate("", xy=(-0.4, 0.04), xycoords=trans,
                      xytext=(2.5, 0.04), fontsize=12, color='#800000', weight='bold',
                      va="center", ha="center",
                      bbox=dict(boxstyle="round", fc="w", alpha=0),
                 arrowprops=dict(arrowstyle="-", color='#800000', lw=1.4))

    sns.boxplot(QoEMacroDF,ax=ax0, showfliers=False)

    plt.show()
    plt.close(fig)

if False:

    QoEMacroDF = pd.DataFrame()
    QoEMacroDF['Verizon'] = LiDARDataDF[(LiDARDataDF['net.interface.cellular[].homeoperator'].str.contains('Verizon')) &
                                          (LiDARDataDF['Sensor-ID'] == 2379) &
                                          (LiDARDataDF['Test-ID'].isin([23, 24]))].reset_index()['Send-Receive-Timings (Seconds)']
    QoEMacroDF['T-Mobile'] = LiDARDataDF[(LiDARDataDF['net.interface.cellular[].homeoperator'].str.contains('T-Mobile')) &
                                          (LiDARDataDF['Sensor-ID'] == 2379) &
                                          (LiDARDataDF['Test-ID'].isin([9,10]))].reset_index()['Send-Receive-Timings (Seconds)']
    #QoEMacroDF['AT&T'] = CameraDataDF[(CameraDataDF['net.interface.cellular[].homeoperator'].str.contains('AT&T')) &
    #                                      (CameraDataDF['Sensor-ID'] == 'camera-4') &
    #                                      (CameraDataDF['Test-ID'].isin([61,62]))].reset_index()['Frame-Time-With-First-Frame-Delay(s)']

    fig = plt.figure(figsize=(5, 4))
    gs1 = gridspec.GridSpec(1, 1, wspace=0.2, hspace=0.08, top=.94, bottom=0.23, left=0.2, right=0.99, figure=fig)
    ax0 = plt.subplot(gs1[0])
    ax0.set_ylim(0, 2.5)
    ax0.set_yticks([i for i in np.arange(0, 2.5, 0.2)])
    ax0.set_ylabel('Frame Delay (s)', fontsize=12)

    #ax0.set_xlabel('Frame Number', fontsize=13)

    trans = ax0.get_xaxis_transform()
    ax0.text(0.12, 0.12, 'Ideal', color='#800000', fontweight='bold')
    ax0.annotate("", xy=(-0.4, 0.04), xycoords=trans,
                      xytext=(2.5, 0.04), fontsize=12, color='#800000', weight='bold',
                      va="center", ha="center",
                      bbox=dict(boxstyle="round", fc="w", alpha=0),
                 arrowprops=dict(arrowstyle="-", color='#800000', lw=1.4))

    sns.boxplot(QoEMacroDF,ax=ax0, showfliers=False)

    plt.show()
    plt.close(fig)

# ========================================================
# Graphing the Sensors

# ========================================================

if False:
    QoESampleDF = pd.DataFrame()

    QoESampleDF['Verizon'] = SensorDataDF[(SensorDataDF['Carrier'].str.contains('Verizon')) &
                                          (SensorDataDF['Sensor'] == 4002) &
                                          (SensorDataDF['Test-ID'] == 19)].reset_index().iloc[:3000]['2']
    QoESampleDF['T-Mobile'] = SensorDataDF[(SensorDataDF['Carrier'].str.contains('T-Mobile')) &
                                          (SensorDataDF['Sensor'] == 4002) &
                                          (SensorDataDF['Test-ID'] == 6)].reset_index().iloc[:3000]['2']


    fig = plt.figure(figsize=(5, 4))
    gs1 = gridspec.GridSpec(1, 1, wspace=0.2, hspace=0.08, top=.94, bottom=0.23, left=0.2, right=0.99, figure=fig)
    ax0 = plt.subplot(gs1[0])
    ax0.set_ylabel('RTT (Seconds)', fontsize=12)
    ax0.set_ylim(0, 2.5)
    ax0.set_yticks([i for i in np.arange(0, 2.5, 0.2)])
    ax0.set_xlabel('Samples over time', fontsize=13)
    sns.lineplot(QoESampleDF,ax=ax0)

    trans = ax0.get_xaxis_transform()
    ax0.text(0.12, 0.12, 'Ideal', color='#800000', fontweight='bold')
    ax0.annotate("", xy=(0.1, 0.04), xycoords=trans,
                      xytext=(7000.5, 0.04), fontsize=12, color='#800000', weight='bold',
                      va="center", ha="center",
                      bbox=dict(boxstyle="round", fc="w", alpha=0),
                 arrowprops=dict(arrowstyle="-", color='#800000', lw=1.4))

    plt.show()
    plt.close(fig)


if False:

    QoEMacroDF = pd.DataFrame()
    QoEMacroDF['Verizon'] = SensorDataDF[(SensorDataDF['Carrier'].str.contains('Verizon')) &
                                          (SensorDataDF['Sensor'] == 4002) &
                                          (SensorDataDF['Test-ID'].isin([15, 16]))].reset_index()['2']
    QoEMacroDF['T-Mobile'] = SensorDataDF[(SensorDataDF['Carrier'].str.contains('T-Mobile')) &
                                          (SensorDataDF['Sensor'] == 4002) &
                                          (SensorDataDF['Test-ID'].isin([4,5]))].reset_index()['2']

    fig = plt.figure(figsize=(5, 4))
    gs1 = gridspec.GridSpec(1, 1, wspace=0.2, hspace=0.08, top=.94, bottom=0.23, left=0.2, right=0.99, figure=fig)
    ax0 = plt.subplot(gs1[0])
    ax0.set_ylim(0, 1.0)
    ax0.set_yticks([i for i in np.arange(0, 1.0, 0.1)])
    ax0.set_ylabel('RTT (s)', fontsize=12)

    #ax0.set_xlabel('Frame Number', fontsize=13)

    trans = ax0.get_xaxis_transform()
    ax0.text(0.12, 0.12, 'Ideal', color='#800000', fontweight='bold')
    ax0.annotate("", xy=(-0.4, 0.1), xycoords=trans,
                      xytext=(2.5, 0.1), fontsize=12, color='#800000', weight='bold',
                      va="center", ha="center",
                      bbox=dict(boxstyle="round", fc="w", alpha=0),
                 arrowprops=dict(arrowstyle="-", color='#800000', lw=1.4))

    sns.boxplot(QoEMacroDF,ax=ax0, showfliers=False)

    plt.show()
    plt.close(fig)
