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

# ================================================================

AnalysisDir = '/home/jason/Analysis-2/rawData/VERIZON-DRIVING-VIDEO-COUNT-1-M1.txt'
XCALEXports = glob.glob(AnalysisDir)


# ================================================================
# Graph the allocation of RBs with respect to the maximum

for xcalFile in XCALEXports:

    testDF = pd.read_csv(xcalFile, sep='\t')
    print(testDF['Event Technology'].unique())
    carrier = testDF.dropna(subset=['Smart Phone Android System Info Operator'])['Smart Phone Android System Info Operator'].unique()
    print(testDF.columns)

    #try:
    #    testDF = testDF.dropna(subset=['ML1 CA Metrics Config Info Carrier Configuration PCell UL Bandwidth'])
    #    print(testDF['Event Technology'].unique())
    #    print(testDF['ML1 CA Metrics Config Info Carrier Configuration PCell UL Bandwidth'].unique())
    #except:
    #    pass

    #try:
        #testDF = testDF.dropna(subset=['Qualcomm Lte/LteAdv Intrafreq Measure Total UL Bandwidth [MHz]'])
        #print(testDF['Event Technology'].unique())
        #print(testDF['Qualcomm Lte/LteAdv Intrafreq Measure Total UL Bandwidth [MHz]'].unique())
    #except:
    #    pass


    QoESampleDF = pd.DataFrame()

    carrierLabel = carrier[0]

    try:
        QoESampleDF[carrierLabel] = testDF['5G KPI Total Info Layer1 UL RB Num(Including 0)'].dropna()
        QoESampleDF = QoESampleDF.reset_index(drop=True).iloc[:200]
        #QoESampleDF[carrierLabel] = testDF['5G KPI PCell RF CQI'].dropna()
    except:
        pass

    try:
        QoESampleDF[carrierLabel] = testDF['LTE KPI PCell PUSCH PRB Number(Including 0)'].dropna()
        QoESampleDF = QoESampleDF.reset_index(drop=True).iloc[:200]
        #QoESampleDF[carrierLabel] = testDF['LTE KPI PCell WB CQI CW0'].dropna()
    except:
        pass


    fig = plt.figure(figsize=(5, 4))
    gs1 = gridspec.GridSpec(1, 1, wspace=0.2, hspace=0.08, top=.94, bottom=0.23, left=0.2, right=0.99, figure=fig)
    ax0 = plt.subplot(gs1[0])
    ax0.set_ylabel('RBs', fontsize=12)
    #ax0.set_ylim(0, 2.5)
    #ax0.set_yticks([i for i in np.arange(0, 2.5, 0.2)])
    ax0.set_xlabel('Sample', fontsize=13)
    sns.lineplot(QoESampleDF,ax=ax0)

    plt.show()
    plt.close(fig)




