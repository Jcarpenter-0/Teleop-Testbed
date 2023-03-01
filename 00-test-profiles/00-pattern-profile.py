import json

# =======================================================
# Simply, take a template, and pattern it with variables to speed up making new consistent entries
# =======================================================
TemplateProfile = 'profile-template-phone-cloud-server-target.json'
OutputName = './profile-X-testing-phone-X.json'
Inserts = ['X']
templateFP = open(TemplateProfile, 'r')
TemplateDict = json.load(templateFP)
templateFP.close()
# =======================================================

for key in TemplateDict.keys():

    value = TemplateDict[key]

    value = value.format(Inserts)

    TemplateDict[key] = value

outFileFP = open(OutputName, 'w')
json.dump(TemplateDict, outFileFP, indent=30)
outFileFP.flush()
outFileFP.close()
