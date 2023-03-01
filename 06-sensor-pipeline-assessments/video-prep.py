import glob
import os
import shutil
import subprocess

# ===========================================================
# Convert videos to varying qualities for use
# ===========================================================
VideoFrameInputFolders = '../../../Datasets/Image-Classifiers-Data/Rural/RGB-Camera/Raw/'
VideoOutputFolder = '../../../Datasets/sensor-inputs-export/'
BaseFrameRate = '30'
TargetCRFs = ['23','26','30','35','40','45','50']
TargetFrameRates = ['15','12','10']
FrameToVideoCommand = "ffmpeg -r {} -pattern_type glob -i {}*.jpg -c:v libx264 -pix_fmt yuv420p -crf {} {}"
VideoConversionCommand = "ffmpeg -i {} -filter:v fps={} {}"
# ===========================================================

videoFrameFolders = glob.glob(VideoFrameInputFolders)

for frameFolder in videoFrameFolders:

    originalVideoName = '-'.join(frameFolder.split('/')[-4:])

    for crf in TargetCRFs:

        basefilename = '{}crf-{}-fps-{}-{}.mp4'.format(VideoOutputFolder, crf, BaseFrameRate,originalVideoName)
        # Make the root video
        try:
            os.remove(basefilename)
        except:
            pass
        videoProc = subprocess.Popen(
            FrameToVideoCommand.format(BaseFrameRate, frameFolder, crf, basefilename).split(' '),
            universal_newlines=False)
        videoProc.wait()

        # Then make new framerate videos from this, otherwise going straight from images makes for an overall "slower video"

        for framerate in TargetFrameRates:
            filename = '{}crf-{}-fps-{}-{}.mp4'.format(VideoOutputFolder, crf, framerate, originalVideoName)

            try:
                os.remove(filename)
            except:
                pass
            videoProc = subprocess.Popen(VideoConversionCommand.format(basefilename, framerate, filename).split(' '), universal_newlines=False)
            videoProc.wait()







