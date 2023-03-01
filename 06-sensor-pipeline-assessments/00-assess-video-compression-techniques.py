import glob
import subprocess
import pandas as pd
import time
import os
import shutil
import datetime
from skimage.metrics import structural_similarity as ssim
import cv2

# =======================================================
# Doing single frame compression for video streaming assessment
# NOTE: these are for understanding the POSSIBLE impact on timing, when in use for streaming
# https://ottverse.com/what-is-cbr-vbr-crf-capped-crf-rate-control-explained/#Variable_Bitrate_Encoding_VBR
# =======================================================

FrameInputDir = '../../../Datasets/sensor-inputs/MnCAV/Vehicle-Cameras/Raw/*.jpg'
FramesToProcess = glob.glob(FrameInputDir)
VideoInputDir = '../../../Datasets/sensor-inputs/MnCAV/Vehicle-Cameras/output-f.mp4'
VideosToProcess = glob.glob(VideoInputDir)

EncodingSchemes = []
# CRF
EncodingSchemes.append('ffmpeg -hide_banner -benchmark -i {} -vcodec libx264 -crf 18 -preset ultrafast -tune zerolatency -r 30 test-video.mp4')
EncodingSchemes.append('ffmpeg -hide_banner -benchmark -i {} -vcodec libx264 -crf 23 -preset ultrafast -tune zerolatency -r 30 test-video.mp4')
EncodingSchemes.append('ffmpeg -hide_banner -benchmark -i {} -vcodec libx264 -crf 30 -preset ultrafast -tune zerolatency -r 30 test-video.mp4')
EncodingSchemes.append('ffmpeg -hide_banner -benchmark -i {} -vcodec libx264 -crf 40 -preset ultrafast -tune zerolatency -r 30 test-video.mp4')
EncodingSchemes.append('ffmpeg -hide_banner -benchmark -i {} -vcodec libx264 -crf 50 -preset ultrafast -tune zerolatency -r 30 test-video.mp4')

EncodingSchemes.append('ffmpeg -hide_banner -benchmark -i {} -vcodec libx265 -crf 18 -preset ultrafast -tune zerolatency -r 30 test-video.mp4')
EncodingSchemes.append('ffmpeg -hide_banner -benchmark -i {} -vcodec libx265 -crf 23 -preset ultrafast -tune zerolatency -r 30 test-video.mp4')
EncodingSchemes.append('ffmpeg -hide_banner -benchmark -i {} -vcodec libx265 -crf 30 -preset ultrafast -tune zerolatency -r 30 test-video.mp4')
EncodingSchemes.append('ffmpeg -hide_banner -benchmark -i {} -vcodec libx265 -crf 40 -preset ultrafast -tune zerolatency -r 30 test-video.mp4')
EncodingSchemes.append('ffmpeg -hide_banner -benchmark -i {} -vcodec libx265 -crf 50 -preset ultrafast -tune zerolatency -r 30 test-video.mp4')

# CCRF
EncodingSchemes.append('ffmpeg -hide_banner -benchmark -i {} -vcodec libx264 -crf 18 -maxrate 8000K -bufsize 10000K -preset ultrafast -tune zerolatency -r 30 test-video.mp4')
EncodingSchemes.append('ffmpeg -hide_banner -benchmark -i {} -vcodec libx264 -crf 23 -maxrate 8000K -bufsize 10000K -preset ultrafast -tune zerolatency -r 30 test-video.mp4')
EncodingSchemes.append('ffmpeg -hide_banner -benchmark -i {} -vcodec libx264 -crf 30 -maxrate 8000K -bufsize 10000K -preset ultrafast -tune zerolatency -r 30 test-video.mp4')
EncodingSchemes.append('ffmpeg -hide_banner -benchmark -i {} -vcodec libx264 -crf 40 -maxrate 8000K -bufsize 10000K -preset ultrafast -tune zerolatency -r 30 test-video.mp4')
EncodingSchemes.append('ffmpeg -hide_banner -benchmark -i {} -vcodec libx264 -crf 50 -maxrate 8000K -bufsize 10000K -preset ultrafast -tune zerolatency -r 30 test-video.mp4')

EncodingSchemes.append('ffmpeg -hide_banner -benchmark -i {} -vcodec libx265 -crf 18 -maxrate 8000K -bufsize 10000K -preset ultrafast -tune zerolatency -r 30 test-video.mp4')
EncodingSchemes.append('ffmpeg -hide_banner -benchmark -i {} -vcodec libx265 -crf 23 -maxrate 8000K -bufsize 10000K -preset ultrafast -tune zerolatency -r 30 test-video.mp4')
EncodingSchemes.append('ffmpeg -hide_banner -benchmark -i {} -vcodec libx265 -crf 30 -maxrate 8000K -bufsize 10000K -preset ultrafast -tune zerolatency -r 30 test-video.mp4')
EncodingSchemes.append('ffmpeg -hide_banner -benchmark -i {} -vcodec libx265 -crf 40 -maxrate 8000K -bufsize 10000K -preset ultrafast -tune zerolatency -r 30 test-video.mp4')
EncodingSchemes.append('ffmpeg -hide_banner -benchmark -i {} -vcodec libx265 -crf 50 -maxrate 8000K -bufsize 10000K -preset ultrafast -tune zerolatency -r 30 test-video.mp4')

# CBR
EncodingSchemes.append('ffmpeg -hide_banner -benchmark -i {} -b:v 4456K -maxrate 8000K -minrate 4000K -bufsize 10000K -vcodec libx264 -preset ultrafast -tune zerolatency -r 30 test-video.mp4')
EncodingSchemes.append('ffmpeg -hide_banner -benchmark -i {} -b:v 4456K -maxrate 8000K -minrate 4000K -bufsize 10000K -vcodec libx265 -preset ultrafast -tune zerolatency -r 30 test-video.mp4')
EncodingSchemes.append('ffmpeg -hide_banner -benchmark -i {} -b:v 4456K -maxrate 6000K -minrate 4000K -bufsize 5000K -vcodec libx264 -preset ultrafast -tune zerolatency -r 30 test-video.mp4')
EncodingSchemes.append('ffmpeg -hide_banner -benchmark -i {} -b:v 4456K -maxrate 6000K -minrate 4000K -bufsize 5000K -vcodec libx265 -preset ultrafast -tune zerolatency -r 30 test-video.mp4')

# ========================================================

DoFrameCalculations = False
DoVideoCalculations = True

# ========================================================

reportDF = pd.DataFrame()
videoReportDF = pd.DataFrame()

# approach, original size, original bitrate, new size, new bitrate, PSNR, SSIM, encode-time


# ========================================================

if DoFrameCalculations:

    for frame in FramesToProcess[0:1]:
        for schemeNum, scheme in enumerate(EncodingSchemes):
            print('Scheme {}/{} {}'.format(schemeNum,len(EncodingSchemes)-1, scheme))
            try:
                os.remove('./test-video.mp4')
            except:
                pass

            try:
                os.remove('./out-frame.png')
            except:
                pass

            ffmpegProc = subprocess.Popen(scheme.format(frame),stdout=subprocess.PIPE,stderr=subprocess.PIPE, shell=True)
            ffmpegProc.wait()
            traceRaw = ffmpegProc.stdout.readlines()
            traceRaw2 = ffmpegProc.stderr.readlines()
            origBrline = traceRaw2[1].decode().replace('\n','').split(' ')[-2]
            if 'libx264' in scheme:
                procTime = traceRaw2[20].decode().replace('\n', '').replace(',',' ').split(' ')[-1]
                brLine = traceRaw2[-1].decode().replace('\n','').split(' ')[-1].split(':')[-1]
            else:
                procTime = traceRaw2[-6].decode().replace('\n', '').replace(',',' ').split(' ')[-1]
                brLine = traceRaw2[-4].decode().replace('\n', '').strip().split(' ')[-1].split(':')[-1]

            # Get the PSNR and SSIM of the single frame image
            ffmpegProc = subprocess.Popen('ffmpeg -i ./test-video.mp4 -vf "select=eq(n\,0)" -vframes 1 out-frame.png',stdout=subprocess.PIPE,stderr=subprocess.PIPE, shell=True)
            ffmpegProc.wait()

            # Import images
            image1 = cv2.imread(frame)
            image2 = cv2.imread('./out-frame.png', 1)

            # Convert the images to grayscale
            gray1 = cv2.cvtColor(image1, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.cvtColor(image2, cv2.COLOR_BGR2GRAY)

            ssimVal = ssim(gray1, gray2)
            psnrVal = cv2.PSNR(gray1, gray2)

            reportRow = pd.DataFrame()
            reportRow['Scheme'] = [scheme]
            reportRow['Approx Encode Time (S)'] = [procTime.replace('s','').split('=')[-1]]
            reportRow['Bitrate Kbps (pre)'] = [origBrline]
            reportRow['Bitrate Kbps (post)'] = [brLine]
            reportRow['Compression (%)'] = [float(brLine)/float(origBrline)]
            reportRow['PSNR'] = [psnrVal]
            reportRow['SSIM'] = [ssimVal]

            reportDF = pd.concat([reportDF, reportRow])

    reportDF.to_csv('./frame-compression-report.csv', index=False)


if DoVideoCalculations:

    for video in VideosToProcess:
        for schemeNum, scheme in enumerate(EncodingSchemes):
            print('Scheme {}/{} {}'.format(schemeNum,len(EncodingSchemes)-1, scheme))
            try:
                os.remove('./test-video.mp4')
            except:
                pass

            ffmpegProc = subprocess.Popen(scheme.format(video),stdout=subprocess.PIPE,stderr=subprocess.PIPE, shell=True)
            ffmpegProc.wait()
            traceRaw = ffmpegProc.stdout.readlines()
            traceRaw2 = ffmpegProc.stderr.readlines()
            origBrline = traceRaw2[7].decode().replace('\n','').split(' ')[-11]
            if 'libx264' in scheme:
                procTime = traceRaw2[33].decode().replace('\n', '').replace(',',' ').split(' ')[-1]
                brLine = traceRaw2[-1].decode().replace('\n','').split(' ')[-1].split(':')[-1]
            else:
                procTime = traceRaw2[45].decode().replace('\n', '').replace(',',' ').split(' ')[-1]
                brLine = traceRaw2[-4].decode().replace('\n', '').strip().split(' ')[-1].split(':')[-1]


            # PSNR Value
            ffmpegPSNRProc = subprocess.Popen(
                ['ffmpeg', '-i', './test-video.mp4', '-i', video, '-lavfi',
                 'psnr=stats_file=./psnr.txt', '-f', 'null', '-'], stderr=subprocess.PIPE)
            ffmpegPSNRProc.wait()
            psnrresultText = ffmpegPSNRProc.stderr.readlines()
            psnrResult = psnrresultText[-1].decode()
            psnrAvg = float(psnrResult.split(' ')[-3].split(':')[-1])

            ffmpegSSIMProc = subprocess.Popen(
                ['ffmpeg', '-i', './test-video.mp4', '-i', video, '-lavfi',
                 'ssim=stats_file=./ssim.txt','-f', 'null', '-'], stderr=subprocess.PIPE)
            ffmpegSSIMProc.wait()
            ssimresultText = ffmpegSSIMProc.stderr.readlines()
            ssimResult = ssimresultText[-1].decode()
            ssimAvg = float(ssimResult.split(' ')[-2].split(':')[-1])

            # ffprobe -v error -select_streams v:0 -count_frames -show_entries stream=nb_read_frames -print_format csv output-f.mp4
            ffprobeFrameCountProc = subprocess.Popen(
                ['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-count_frames', '-show_entries', 'stream=nb_read_frames', '-print_format', 'csv', video], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            ffprobeFrameCountProc.wait()
            frameCountText = ffprobeFrameCountProc.stdout.readlines()
            frameCount = int(frameCountText[0].decode().split(',')[-1])

            reportRow = pd.DataFrame()
            reportRow['Scheme'] = [scheme]
            reportRow['Approx Encode Time (S)'] = [procTime.replace('s','').split('=')[-1]]
            reportRow['Bitrate Kbps (pre)'] = [origBrline]
            reportRow['Bitrate Kbps (post)'] = [brLine]
            reportRow['Compression (%)'] = [float(brLine)/float(origBrline)]
            reportRow['Frame-Count'] = [frameCount]
            reportRow['PSNR'] = [psnrAvg]
            reportRow['SSIM'] = [ssimAvg]

            videoReportDF = pd.concat([videoReportDF, reportRow])


    videoReportDF.to_csv('./video-compression-report.csv', index=False)
