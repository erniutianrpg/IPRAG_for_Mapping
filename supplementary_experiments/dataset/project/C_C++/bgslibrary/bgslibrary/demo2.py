##############################################
# Demo file
# python demo2.py --- will use video
# python demo2.py image --- will use images
#############################################

import numpy as np
import cv2
import pybgs as bgs
import sys
import glob

print("OpenCV Version: {}".format(cv2.__version__))

## bgslibrary algorithms
algorithms=[]
algorithms.append(bgs.FrameDifference())
algorithms.append(bgs.StaticFrameDifference())
algorithms.append(bgs.WeightedMovingMean())
algorithms.append(bgs.WeightedMovingVariance())
algorithms.append(bgs.AdaptiveBackgroundLearning())
algorithms.append(bgs.AdaptiveSelectiveBackgroundLearning())
algorithms.append(bgs.MixtureOfGaussianV2())
algorithms.append(bgs.PixelBasedAdaptiveSegmenter())
algorithms.append(bgs.SigmaDelta())
algorithms.append(bgs.SuBSENSE())
algorithms.append(bgs.LOBSTER())
algorithms.append(bgs.PAWCS())
algorithms.append(bgs.TwoPoints())
algorithms.append(bgs.ViBe())
algorithms.append(bgs.CodeBook())
algorithms.append(bgs.FuzzySugenoIntegral())
algorithms.append(bgs.FuzzyChoquetIntegral())
algorithms.append(bgs.LBSimpleGaussian())
algorithms.append(bgs.LBFuzzyGaussian())
algorithms.append(bgs.LBMixtureOfGaussians())
algorithms.append(bgs.LBAdaptiveSOM())
algorithms.append(bgs.LBFuzzyAdaptiveSOM())
algorithms.append(bgs.VuMeter())
algorithms.append(bgs.KDE())
algorithms.append(bgs.IndependentMultimodal())

# The algorithms below are compiled into pybgs only for certain OpenCV versions.
# Which ones are available depends on the OpenCV that pybgs was COMPILED against
# (not on cv2.__version__, the opencv-python build). Add each one only if this
# pybgs build actually exposes it, so the demo never raises AttributeError.
for name in [
    "MixtureOfGaussianV1", "GMG",          # OpenCV 2.x only
    "KNN",                                  # OpenCV > 2
    "DPAdaptiveMedian", "DPGrimsonGMM", "DPZivkovicAGMM", "DPMean", "DPWrenGA",
    "DPPratiMediod", "DPEigenbackground", "DPTexture",
    "T2FGMM_UM", "T2FGMM_UV", "T2FMRF_UM", "T2FMRF_UV", "MultiCue",  # OpenCV 2.x/3.x only
    "LBP_MRF", "MultiLayer",               # OpenCV 2.x / <= 3.4.7 only
  ]:
  if hasattr(bgs, name):
    algorithms.append(getattr(bgs, name)())
  else:
    print("skipping (not available in this pybgs build):", name)


# check if we want to use the images
image = False
if (len(sys.argv) == 2):
    if(sys.argv[1] == "image"):
        image = True
        img_folder = "dataset/frames"
        img_array = sorted(glob.iglob(img_folder + '/*.png'))

video_file = "dataset/video.avi"

print("Number of available algorithms: ", len(algorithms))
for algorithm in algorithms:
  print("Running ", algorithm.__class__)

  if(image):
    # loop x times as files in our folder
    for x in range(0, len(img_array)):

        # we can loop now through our array of images
        img_path = img_array[x]

        # read file into open cv and apply to algorithm to generate background model
        img = cv2.imread(img_path)
        img_output = algorithm.apply(img)
        img_bgmodel = algorithm.getBackgroundModel()

        # show images in python imshow window
        cv2.imshow('image', img)
        cv2.imshow('img_output', img_output)
        cv2.imshow('img_bgmodel', img_bgmodel)

        # we need waitKey otherwise it wont display the image
        if 0xFF & cv2.waitKey(10) == 27:
          break

        # Comment out to save images to bg and fg folder
        #img_bg = img_path.replace(img_folder, "output/bg")
        #img_fg = img_path.replace(img_folder, "output/fg")
        #cv2.imwrite(img_bg, img_bgmodel)
        #cv2.imwrite(img_fg, img_output)

        print("Frames left: " + str(len(img_array)-x))

  else:

      capture = cv2.VideoCapture(video_file)
      while not capture.isOpened():
        capture = cv2.VideoCapture(video_file)
        cv2.waitKey(1000)
        print("Wait for the header")

      #pos_frame = capture.get(cv2.cv.CV_CAP_PROP_POS_FRAMES)
      #pos_frame = capture.get(cv2.CV_CAP_PROP_POS_FRAMES)
      pos_frame = capture.get(1)
      while True:
        flag, frame = capture.read()

        if flag:
          cv2.imshow('video', frame)
          #pos_frame = capture.get(cv2.cv.CV_CAP_PROP_POS_FRAMES)
          #pos_frame = capture.get(cv2.CV_CAP_PROP_POS_FRAMES)
          pos_frame = capture.get(1)
          #print str(pos_frame)+" frames"

          img_output = algorithm.apply(frame)
          img_bgmodel = algorithm.getBackgroundModel()

          cv2.imshow('img_output', img_output)
          cv2.imshow('img_bgmodel', img_bgmodel)

        else:
          #capture.set(cv2.cv.CV_CAP_PROP_POS_FRAMES, pos_frame-1)
          #capture.set(cv2.CV_CAP_PROP_POS_FRAMES, pos_frame-1)
          #capture.set(1, pos_frame-1)
          #print "Frame is not ready"
          cv2.waitKey(1000)
          break

        if 0xFF & cv2.waitKey(10) == 27:
          break

        #if capture.get(cv2.cv.CV_CAP_PROP_POS_FRAMES) == capture.get(cv2.cv.CV_CAP_PROP_FRAME_COUNT):
        #if capture.get(cv2.CV_CAP_PROP_POS_FRAMES) == capture.get(cv2.CV_CAP_PROP_FRAME_COUNT):
        #if capture.get(1) == capture.get(cv2.CV_CAP_PROP_FRAME_COUNT):
          #break

print("Finished")
cv2.destroyAllWindows()
