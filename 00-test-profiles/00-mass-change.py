import glob
import os

# =====================================================
# Changing single text elements in all files
# =====================================================
ReplaceText = ''
NewText = ''
Files = glob.glob('./profile-*-phone-*.json')
# =====================================================


for file in Files:
    fileFP = open(file,'r')
    fileData = fileFP.read()
    fileData = fileData.replace(ReplaceText, NewText)
    fileFP.close()

    newFileFP = open(file, 'w')
    newFileFP.write(fileData)
    newFileFP.flush()
    newFileFP.close()
    print()
