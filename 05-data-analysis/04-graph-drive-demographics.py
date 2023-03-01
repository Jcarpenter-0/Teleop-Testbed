import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

fullDataDF = pd.read_csv('../00-sensor-sources/data-analysis/full-sensor-data.csv')

# =========================================================================
rowAverageCount = 40
print('Dataset Size {}'.format(len(fullDataDF)))
# =========================================================================
# Graph the number of people and cars seen by day

axes = plt.gca()
shortenedTable = fullDataDF.groupby(np.arange(len(fullDataDF))//rowAverageCount).mean()
shortenedTable.plot(kind='line', y='People-Count', ax=axes)
shortenedTable.plot(kind='line', y='Car-Count', ax=axes)
axes.set_ylabel('Count')
axes.set_xlabel('Time (s*{})'.format(rowAverageCount))
plt.suptitle('')
plt.title('Drive Demographics')
plt.tight_layout()
plt.savefig('./data-analysis/lineplot-people-cars.png')
plt.close()
