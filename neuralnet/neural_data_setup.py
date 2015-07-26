import os
import subprocess
import pdb
import math
import random
import getopt
import sys
import csv
import numpy as np
import cv2
from scipy import misc, ndimage #load images
from collections import defaultdict
import sklearn.utils

import get_data
from get_data import DataLoader
from augmentation import DataAugmentation
import utils

'''
ViolaDataSetup is used to:
    - setup the training patches for viola
    - produce the corresponding .dat and .vec files
The .vec files are needed to train a cascade from the ViolaTrainer class
'''


class NeuralDataLoad(object):
    def __init__(self, viola_detector_data = None):
        self.viola_detector_data = 'combo9_min_neighbors3_scale1.08_groupNone_rotateTrue_removeOffTrue' if viola_detector_data is None else viola_detector_data
        self.background_FP_viola_path = '../data_original/training/neural/{0}/falsepos_from_viola_training/'.format(self.viola_detector_data)
        self.thatch_metal_TP_viola_path = '../data_original/training/neural/{0}/truepos_from_viola_training/'.format(self.viola_detector_data)

    def load_data(self):
        self.ground_truth_metal_thatch = DataLoader.get_all_patches_folder(merge_imgs=True)
        self.viola_metal_thatch = self.get_viola_positive_patches(self.thatch_metal_TP_viola_path)
        self.viola_background = self.get_viola_background_patches(self.background_FP_viola_path)
        total_length = self.count_patches_helper()

        self.X = np.empty((total_length, 3, utils.PATCH_W, utils.PATCH_H), dtype='float32')
        self.y = np.empty((total_length), dtype='int32')
        self.failed_patches = 0

        #process the metal and thatch
        index = 0 
        for roof_type in ['metal', 'thatch']:
            label = utils.ROOF_LABEL[roof_type]
            for data_source in [self.ground_truth_metal_thatch[roof_type], self.viola_metal_thatch[roof_type]]: 
                for patch in data_source:
                    index = self.process_patch(patch, label, index)                    

        #process the background
        label = utils.ROOF_LABEL['background']
        for patch in self.viola_background:
            index = self.process_patch(patch, label, index)

        #here we can add more random negative patches if needed

        #remove the end if index<len(X) -- some patches failed to load
        self.X = self.X[:index, :,:,:]
        self.X = self.X.astype(np.float32)

        self.X, self.y = sklearn.utils.shuffle(self.X, self.y, random_state=42)  # shuffle train data    
        return self.X, self.y


    def get_viola_positive_patches(self, path):
        #lok at the viola folder, get all of the jpg.s depending on what roof_type the image name contains
        viola_metal_thatch = defaultdict(list)
        for file in os.listdir(self.thatch_metal_TP_viola_path):
            if file.endswith('.jpg'):
                patch = cv2.imread(path+file)
                if 'metal' in file.lower():
                    viola_metal_thatch['metal'].append(patch) 
                elif 'thatch' in file.lower():
                    viola_metal_thatch['thatch'].append(patch)
        return viola_metal_thatch


    def get_viola_background_patches(self, path): 
        background_FP_viola_path = list()
        for file in os.listdir(path):
            if file.endswith('.jpg'):
                if 'background' in file.lower():
                    patch = cv2.imread(self.background_FP_viola_path+file)
                    background_FP_viola_path.append(patch) 
        return background_FP_viola_path 


    def process_patch(self, patch, label, index):
        x = np.asarray(patch, dtype='float32')/255
        try:
            x = utils.resize_rgb(x)
            x = x.transpose(2,0,1)
            x.shape = (1, x.shape[0], x.shape[1], x.shape[2])
            self.X[index, :, :, :] = x
        except ValueError, e:
            print e
            self.failed_patches += 1
            print 'fail:'+ str(failures)
        else:
            self.y[index] = label
            index += 1
        return index 


    def count_patches_helper(self):
        total_length = 0 
        for roof_type in utils.ROOF_TYPES:
            total_length += len(self.viola_metal_thatch[roof_type])
            total_length += len(self.ground_truth_metal_thatch[roof_type])
        total_length += len(self.viola_background)
        return total_length

    @staticmethod
    def save_img(x,y,i, other_text=''):
        x = x*255
        x = x.transpose(1,2,0)
        cv2.imwrite('check_load_neural/{2}_img{0}_label{1}.jpg'.format(i, y[i], other_text), x)



def main(data_reset=False):
    X, y = NeuralDataLoad().load_data()
    bins = np.bincount(y)
    print bins 
    print X.shape
    print y.shape
    for i in range(X.shape[0]):
        x = X[i, :, :,:]
        NeuralDataLoad.save_img(x,y, i)

if __name__ == '__main__':
    main()

