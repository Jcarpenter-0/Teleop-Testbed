import pandas as pd
import matplotlib.pyplot as plt

#sensorData = pd.read_csv('./MnCAV/mncav-vehicle-demographics.csv')

subDF = pd.read_csv('../00-sensor-sources/MnCAV/intermediate.csv')

#types = sensorData['Type'].unique()
#tputs = []

#for dataType in types:
#    tputs.append(sensorData[sensorData['Type'] == dataType]['Need (Mbps)'].sum())

#subDF['Type'] = types
#subDF['Need (Mbps)'] = tputs
subDF = subDF.set_index('Type')
#subDF.to_csv('./intermediate.csv')

plotAx = subDF.plot.pie(y='Need', autopct='%1.1f%%', fontsize=22, figsize=(8, 7),title=None, explode=[0.05,0.05,0.05,0.25,0.25,0.55,0.05], rotatelabels=True)
plotAx.get_legend().remove()
plotAx.set_ylabel(None)
plt.tight_layout()
plt.savefig('./data-analysis/mncav-vehicle-sensor-demographics.jpg')
plt.close()
