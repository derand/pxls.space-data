#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
#  This script shows gaps beetween bin(include pixel data text) files in directory
#

import time, pytz, datetime
import os, glob, shutil, struct
import gzip
from create_frames import file_time
import argparse

def epoch2human(tm):
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(tm))

def print_times(tm1, tm2):
    if tm1:
        if tm2:
            print '%s - %s  # %d'%(epoch2human(tm1), epoch2human(tm2), tm2-tm1)
        else:
            print '%s -          ...'%epoch2human(tm1)
    else:
        print '         ...        - %s'%epoch2human(tm2)


if __name__=='__main__':
    script_path = os.path.dirname(os.path.realpath(__file__))
    os.chdir(script_path)

    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--data_path',  type=str, default='/mnt/', help="source data path (default: /mnt/)")
    #parser.add_argument('--time_start',       type=int, default=0, help="start time in unixtime format")
    #parser.add_argument('--time_stop',        type=int, default=0, help="stop time in unixtime format")
    args = parser.parse_args()

    data_path = args.data_path


    files = []
    for file in glob.glob("%s*.bin"%data_path):
        files.append(file)
    files.sort(key=lambda el: os.path.basename(el))

    filename = files.pop(0)
    dt = os.path.splitext(os.path.basename(filename))[0]
    tm = file_time(filename)
    print_times(0, tm)
    upxls_fn = '%s.txt'%dt
    if os.path.exists(data_path+upxls_fn):
        with open(data_path+upxls_fn, 'r') as fo:
            for line in fo:
                tmp = line.split(';')
                if len(tmp) == 4:
                    tm = int(tmp[0])

    while len(files) > 0:
        filename = files.pop(0)
        dt = os.path.splitext(os.path.basename(filename))[0]
        tm2 = file_time(filename)
        print_times(tm, tm2)

        upxls_fn = '%s.txt'%dt
        tm = tm2
        if os.path.exists(data_path+upxls_fn):
            with open(data_path+upxls_fn, 'r') as fo:
                for line in fo:
                    tmp = line.split(';')
                    if len(tmp) == 4:
                        tm = int(tmp[0])
    print_times(tm, 0)
