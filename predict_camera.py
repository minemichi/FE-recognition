'''
_ import
'''
#_ my func import
from define_common import *
from define_model import CNN_model
from define_loader import Label_loader, Image_loader
from define_recognition import Recognition

#_ common import
import os
import _pickle as cPickle
import numpy as np
import csv
import sys
import glob
from datetime import datetime
import shutil
import argparse
import random
import copy

#_ cv import
from keras.preprocessing.image import load_img, img_to_array
from PIL import Image#minemichi
import cv2
##import matplotlib.pyplot as plt#minemichi


'''
_ prepar
'''
#_ set arg
parser = argparse.ArgumentParser(description='argparse.')  # command line option lib
parser.add_argument('-vd', type=str, required=False, help='set number of video device.')
parser.add_argument('-sf', type=str, required=False, help='set number of skip frame.')
args = parser.parse_args()
if args.vd:
    video_device = int(args.vd)
else:
    video_device = 0
if args.sf:
    skip_frame = int(args.sf)
else:
    skip_frame = 1
    
#_ Starting built-in cap
cap = cv2.VideoCapture(0)
cascade = cv2.CascadeClassifier(cascade_path)# Get cascade classifier feature quantity

#_ load label
ins_label_loader = Label_loader(label_path)
ins_label_loader.get_labels()
labels = ins_label_loader.labels
labels_num = len(labels)

#_ load model
ins_cnn_model = CNN_model(labels_num, image_size)
model = ins_cnn_model.nisime_kai_gap_model()
model.load_weights(model_path)

#_ create and move directories
if os.path.isdir(capture_image_path) is False:
    os.makedirs(capture_image_path)
for label in labels:
    tmp_path = save_base_path + '/' + label
    if os.path.isdir(tmp_path) is False:
        os.makedirs(tmp_path)

#_ ver
frame_count = 0
save_face_rects = False
#_ ins
ins_recognition = Recognition(model, labels, layer_name)

'''
_ start image acquisition
'''
while True:
    # Get one frame image read from built-in camera
    ret, frame_image = cap.read()

    # Break if the image can not be read.
    if ret is False:
        break
        
    # Execution of face recognition
    face_rects = cascade.detectMultiScale(frame_image, scaleFactor=1.2, minNeighbors=2, minSize=(10, 10))

    # When a face is found, get face-place cv2.rectangle
    if len(face_rects) > 0:

        # skip by skip_frame
        if frame_count % skip_frame == 0:
            # Cutting processing
            ins_recognition.get_face(face_rects, frame_image)
            ins_recognition.predict(select_exp, frame_count)
            #get_faces = ins_recognition.faces
            if select_op['grad_cam'] == 1:
                ins_recognition.grad_cam(select_exp, frame_count)

            # Keep a record
            save_face_rects = face_rects
        else:
            if save_face_rects is False:
                continue
    else:
        if save_face_rects is False:
            continue

    use_rects = save_face_rects
    frame_count += 1

    # Create swapping image
    image_info = []
    swap_info = []
    for for1, (rect, predict, face) in enumerate(zip(use_rects, ins_recognition.predicts, ins_recognition.cv2_faces)):
        image_info.append([rect, predict, face])
        swap_info.append([rect, predict, face])

    if select_op['swap'] == 1:
        # Search select_exp
        swap_idx = [i for i, x in enumerate(swap_info) if x[1] == select_exp]
        if len(swap_idx) != 0:
            swap_idx.insert(0, swap_idx[-1])
            swap_idx.pop()
            swap_default = swap_idx[0]
            swap_iter = iter(swap_idx)

            for for1 in range(int(len(swap_idx) / 2)):
                first_idx, second_idx = next(swap_iter), next(swap_iter)
                swap_info[first_idx][2], swap_info[second_idx][2] =\
                    copy.copy(swap_info[second_idx][2]), copy.copy(swap_info[first_idx][2])
            if len(swap_idx) % 2 != 0:
                first_idx = next(swap_iter)
                swap_info[first_idx][2], swap_info[swap_idx[0]][2] =\
                    copy.copy(swap_info[swap_idx[0]][2]), copy.copy(swap_info[first_idx][2])
        use_info = swap_info
    else:
        use_info = image_info

    # Create a result image
    #for for1, (rect, predict, face) in enumerate(zip(use_rects, ins_recognition.predicts, get_faces)):
    for for1, get_info in enumerate(use_info):
        rect = get_info[0]
        predict = get_info[1]
        face = get_info[2]

        if select_op['face_recognition'] == 1:
            expression_count[predict] += 1

            # If expression mode is true, draw color rect and text
            if select_op['expression_recognition'] == 1:
                cv2.rectangle(frame_image, tuple(rect[0:2]), tuple(rect[0:2] + rect[2:4]),
                              expression_colors[predict],
                              thickness=2)
                cv2.putText(frame_image, labels[predict], (rect[0], rect[1] - 25), cv2.FONT_HERSHEY_COMPLEX,
                            font_size,
                            expression_colors[predict])
            else:
                cv2.rectangle(frame_image, tuple(rect[0:2]), tuple(rect[0:2] + rect[2:4]), (255, 255, 255),
                              thickness=2)

            # If grad_cam mode is true, draw grad_cam image
            if select_op['grad_cam'] == 1:
                # if len(ins_recognition.jetcams) > 0:
                if len(ins_recognition.jetcams) >= for1:
                    frame_image[rect[1]:rect[1] + rect[3], rect[0]:rect[0] + rect[2]] = \
                        cv2.resize(ins_recognition.jetcams[for1], (rect[2], rect[3]), cv2.INTER_NEAREST)

            # If mosaic mode is true, apply a filter to excepted expression.
            if select_op['mosaic'] == 1:
                if predict != select_exp:
                    cut_img = frame_image[rect[1]:rect[1] + rect[3], rect[0]:rect[0] + rect[2]]
                    cut_img = cv2.resize(cut_img, (rect[2] // 20, rect[3] // 20))
                    cut_img = cv2.resize(cut_img, (rect[2], rect[3]), cv2.INTER_NEAREST)
                    frame_image[rect[1]:rect[1] + rect[3], rect[0]:rect[0] + rect[2]] = cut_img

            # If mosaic mode is true, apply a filter to excepted expression.
            if select_op['swap'] == 1:
                if predict == select_exp:
                    cut_img = cv2.resize(face, (rect[2], rect[3]))
                    # cut_img = cv2.resize(cut_img, (rect[2], rect[3]), cv2.INTER_NEAREST)
                    frame_image[rect[1]:rect[1] + rect[3], rect[0]:rect[0] + rect[2]] = cut_img

    # Show image
    expression_total = 0
    for num in expression_count:
         expression_total += num
    for fornum in np.arange(0, 4):
        if select_op['percent'] == 1:
            face_per_tmp1 = int((expression_count[fornum]/expression_total) * 100)
            tmp_mark = '%'
        else:
            face_per_tmp1 = expression_count[fornum]
            tmp_mark = ''
        cv2.putText(frame_image, label[fornum] + ' ' + str(face_per_tmp1) + tmp_mark,
                    (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) - 600 + fornum * 150, 20),
                    cv2.FONT_HERSHEY_COMPLEX, font_size * 0.7, expression_colors[fornum])
    for fornum in np.arange(4, 7):
        if select_op['percent'] == 1:
            face_per_tmp1 = int((expression_count[fornum]/expression_total) * 100)
            tmp_mark = '%'
        elif select_op['percent'] == 1:
            face_per_tmp1 = expression_count[fornum]
            tmp_mark = ''
        cv2.putText(frame_image, label[fornum] + ' ' + str(face_per_tmp1) + 'n',
                    (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) - 600 + (fornum - 4) * 150,
                     int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) - 10),
                    cv2.FONT_HERSHEY_COMPLEX, font_size*0.7, expression_colors[fornum])
    cv2.putText(frame_image, 's_' + label[select_exp],
                (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) - 150,
                 int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) - 10), cv2.FONT_HERSHEY_COMPLEX, font_size*0.7, (255, 255, 255))
    cv2.namedWindow('frame', cv2.WINDOW_KEEPRATIO | cv2.WINDOW_NORMAL)
    cv2.imshow('frame', frame_image)

    # Used command key after press c key
    if cv2.waitKey(1) & 0xFF == ord('c'):
        cv2.putText(frame_image, 'Please command', (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)/3),
                                              int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)/2)),
                    cv2.FONT_HERSHEY_COMPLEX, font_size*2, op_color)
        cv2.imshow('frame', frame_image)
        save_key = cv2.waitKey(5000)
        if  save_key& 0xFF == ord('q'):
            # Exit built-in camera
            break
        elif save_key& 0xFF == ord('0'):
            select_exp = 0
        elif save_key& 0xFF == ord('1'):
            select_exp = 1
        elif save_key& 0xFF == ord('2'):
            select_exp = 2
        elif save_key& 0xFF == ord('3'):
            select_exp = 3
        elif save_key& 0xFF == ord('4'):
            select_exp = 4
        elif save_key& 0xFF == ord('5'):
            select_exp = 5
        elif save_key& 0xFF == ord('6'):
            select_exp = 6
        elif save_key& 0xFF == ord('r'):
            select_op['face_recognition'] = 1-select_op['face_recognition']
        elif save_key& 0xFF == ord('p'):
            select_op['expression_recognition'] = 1-select_op['expression_recognition']
        elif save_key& 0xFF == ord('d'):
            select_op['percent'] = 1-select_op['percent']
        elif save_key& 0xFF == ord('m'):
            select_op['mosaic'] = 1-select_op['mosaic']
        elif save_key& 0xFF == ord('s'):
            select_op['swap'] = 1-select_op['swap']
        elif save_key& 0xFF == ord('g'):
            select_op['grad_cam'] = 1-select_op['grad_cam']
        elif save_key& 0xFF == ord('z'):
            select_op['face_recognition'] = 0
            select_op['expression_recognition'] = 0
            select_op['percent'] = 0
            select_op['mosaic'] = 0
            select_op['grad_cam'] = 0

# Exit built-in camera
cap.release()
cv2.destroyAllWindows()
