import plotly.express as px
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import math


DataDF1 = pd.read_csv('./special-wei-processing/MPLS-DRIVE-DOWNTOWN-RANDOM-OP-M3-1S.csv')
DataDF1["Lon"] = np.multiply(DataDF1["Lon"], 10)
DataDF1["Lat"] = np.multiply(DataDF1["Lat"], 10)

# Data 1 Cleanup
tst = pd.DataFrame()

DataDF2 = pd.read_csv('./special-wei-processing/MPLS-DRIVE-DOWNTOWN-TECH-M2-1S.csv')

# Data 2 Cleanup


data = pd.concat([DataDF1, DataDF2])
data = data.interpolate(method='pad')

#DataFile = './special-wei-processing/MPLS-DRIVE-DOWNTOWN-RANDOM-OP-M3-1S.csv'
#DataFile = './special-wei-processing/MPLS-DRIVE-DOWNTOWN-TECH-M2-1S.csv'
#data = pd.read_csv(DataFile)

#MetricLabel = '5G KPI PCell RF Serving PCI'
#MetricLabel = '5G KPI SCell[1] RF Serving PCI'
#MetricLabel = '5G KPI SCell[2] RF Serving PCI'
MetricLabel = '5G KPI Total Info DL CA Type'
OutputFile = "output/Geo-Fig-{}.pdf".format(MetricLabel)


specficCADF = pd.DataFrame()
specficCADF[MetricLabel] = data[MetricLabel]
specficCADF = specficCADF.dropna(subset=[MetricLabel])


specficCADF[MetricLabel] = specficCADF[MetricLabel].astype(str)
UniqueCATypes = list(specficCADF[MetricLabel].unique())
UniqueCATypes.sort()


#Annotation = 'PCell'
#Annotation = 'SCell[1]'
#Annotation = 'SCell[2]'

#PCellLabel = '5G KPI PCell RF Serving PCI'
#SCell1Label = '5G KPI SCell[1] RF Serving PCI'
#SCell2Label = '5G KPI SCell[2] RF Serving PCI'
#data["Lon"] = np.multiply(data["Lon"], 10)
#data["Lat"] = np.multiply(data["Lat"], 10)
#data = data.dropna(subset=[MetricLabel])

#data[PCellLabel] = data[PCellLabel].astype(str)
#data[SCell1Label] = data[SCell1Label].astype(str)
#data[SCell2Label] = data[SCell2Label].astype(str)

#PCIs = list(data[PCellLabel].unique())
#PCIs.extend(list(data[SCell1Label].unique()))
#PCIs.extend(list(data[SCell2Label].unique()))
#PCIs = np.unique(PCIs)
#PCIs.sort()

#print(len(PCIs))

colorMap = dict()

for pciNum, PCI in enumerate(UniqueCATypes):
    colorMap[PCI] = px.colors.qualitative.Dark24[pciNum%len(px.colors.qualitative.Dark24)]

print(colorMap)

fig = px.scatter_mapbox(data,
                        lat="Lat",
                        lon="Lon",
                        zoom=14.4,
                        color=MetricLabel,
                        # 44.977, -93.2682
                        center={'lat':44.977,'lon':-93.2682},
                        color_discrete_sequence=px.colors.qualitative.Dark24,
                        color_discrete_map=colorMap,
                        height=600,
                        width=800)


fig.update_traces(marker=dict(size=10),selector=dict(mode='markers'))
fig.update_layout(mapbox_style="carto-positron", showlegend=False)
fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
#fig.add_annotation(x=0.9, y=0.90, font=dict(color='red',size=42), bgcolor='lightgrey', bordercolor='lightgrey',
#            text=Annotation)


fig.update_layout(
    legend=dict(
        x=0.0,
        y=0.0,
        traceorder="normal",
        font=dict(
            family="sans-serif",
            size=24,
            color="black"
        ),
    )
)

fig.update_layout(showlegend=True)
fig.write_image(OutputFile)
#fig.show()


