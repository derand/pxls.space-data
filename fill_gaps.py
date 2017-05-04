#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time, pytz, datetime
import os, glob, shutil, struct
import gzip
from create_frames import read_in_chunks, file_time, clear_files
import argparse
import random


def fill_frame(filename, pixels, field_size):
    isize = 0
    if os.stat(filename).st_size == 0:
        return False
    with open(filename, 'rb') as f:
        f.seek(-4, 2)
        isize = struct.unpack('I', f.read(4))[0]
    if isize != field_size[0] * field_size[1]:
        return False

    y = 0
    f = gzip.open(filename)
    for line in read_in_chunks(f, chunk_size=field_size[1]):
        for x in range(len(line)):
            pixels[x][y] = ord(line[x]) & 0x0f
        y += 1
    return True

def save_frame(filename, pixels, field_size):
    with gzip.open(filename, "wb") as f:
        for y in range(field_size[1]):
            data = ''
            for x in range(field_size[0]):
                data = data+chr(pixels[x][y])
                #data.append(chr(pixels[x][y]))
            f.write(data)

def get_diff(pixels1, pixels2, field_size, tm1, tm2):
    diff = []
    if tm1 > tm2:
        tm2 = tm1+1
    for y in range(field_size[1]):
        for x in range(field_size[0]):
            if pixels1[x][y] <> pixels2[x][y]:
                diff.append((random.randrange(tm1, tm2), x, y, pixels2[x][y]))
    return sorted(diff, key=lambda el: el[0])


if __name__=='__main__':
    script_path = os.path.dirname(os.path.realpath(__file__))
    os.chdir(script_path)

    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--field_size', type=str, default='2000:2000', help="filed size width:height (default: 2000:2000)")
    parser.add_argument('-d', '--data_path',  type=str, default='/mnt/', help="source data path (default: /mnt/)")
    parser.add_argument('--time_start',       type=int, default=0, help="start time in unixtime format")
    parser.add_argument('--time_stop',        type=int, default=0, help="stop time in unixtime format")
    parser.add_argument('--clear_bin_files',  action='store_true', help="clear bin files for speed")
    args = parser.parse_args()

    field_size = map(int, args.field_size.split(':'))[0:2]

    data_path = args.data_path

    tm_start = args.time_start
    tm_stop = args.time_stop
    if tm_stop <= tm_start:
        tm_stop = int(time.time())

    clear_bin_files = args.clear_bin_files


    files = []
    for file in glob.glob("%s*.bin"%data_path):
        files.append(file)
    files.sort(key=lambda el: os.path.basename(el))
    files = clear_files(files, tm_start, tm_stop)
    for f in files:
        print f

    pixels = [[0 for i in range(field_size[1])]  for j in range(field_size[0])]
    tmp_pixels = [[0 for i in range(field_size[1])]  for j in range(field_size[0])]

    day_files = {}

    filename = files.pop(0)
    dt = os.path.splitext(os.path.basename(filename))[0]
    day = dt.split('_')[0]
    if day_files.has_key(day):
        day_files[day].append(dt)
    else:
        day_files[day] = [dt,]
    data_frame = fill_frame(filename='%s%s.bin'%(data_path, dt), pixels=pixels, field_size=field_size)
    tmp_fn = '%s.txt'%dt
    fo = open(data_path+tmp_fn, 'a+')
    fo.seek(0)
    tm = file_time(filename)
    if os.path.exists(data_path+tmp_fn):
        while True:
            line = fo.readline()
            if not line:
                break
            tmp = line.split(';')
            if len(tmp) == 4:
                tm = int(tmp[0])
                x = int(tmp[1])
                y = int(tmp[2])
                col = int(tmp[3])
                pixels[x][y] = col & 0x0f


    while len(files) > 1:
        filename = files.pop(0)
        dt = os.path.splitext(os.path.basename(filename))[0]
        day = dt.split('_')[0]
        if day_files.has_key(day):
            day_files[day].append(dt)
        else:
            day_files[day] = [dt,]
        fill_frame(filename='%s%s.bin'%(data_path, dt), pixels=tmp_pixels, field_size=field_size)
        tm2 = file_time(filename)

        #if clear_bin_files:
        #    with open(filename, 'w') as f:
        #        f.write('')

        diff = get_diff(pixels1=pixels, pixels2=tmp_pixels, field_size=field_size, tm1=tm, tm2=tm2)
        print len(diff), tm2-tm, filename

        if len(diff):
            for d in diff:
                pixels[d[1]][d[2]] = d[3]
                s = "{0};{1};{2};{3}\n".format(d[0], d[1], d[2], d[3])
                fo.write(s)

        tmp_fn = '%s.txt'%dt
        if fo:
            fo.close()
        fo = open(data_path+tmp_fn, 'a+')
        fo.seek(0)
        tm = file_time(filename)
        if os.path.exists(data_path+tmp_fn):
            #shutil.copy(data_path+tmp_fn, out_path+tmp_fn)
            while True:
                line = fo.readline()
                if not line:
                    break
                tmp = line.split(';')
                if len(tmp) == 4:
                    tm = int(tmp[0])
                    x = int(tmp[1])
                    y = int(tmp[2])
                    col = int(tmp[3])
                    pixels[x][y] = col & 0x0f
        if tm > tm_stop:
            break
    if fo:
        fo.close()


    # merge day files
    if clear_bin_files:
        while len(files) > 0:
            filename = files.pop(0)
            dt = os.path.splitext(os.path.basename(filename))[0]
            day = dt.split('_')[0]
            if day_files.has_key(day):
                day_files[day].append(dt)
            else:
                day_files[day] = [dt,]
        print day_files

        keys = list(day_files.keys())
        keys.sort()

        for k in keys:
            if len(day_files[k]) > 1:
                f_points = None
                f_users = None
                for i in range(1, len(day_files[k])):
                    tmp_fn = data_path + day_files[k][i] + '.txt'
                    if os.path.exists(tmp_fn):
                        if f_points is None:
                            f_points = open(data_path + day_files[k][0] + '.txt', 'ab+')
                        f_tmp = open(tmp_fn, 'rb')
                        shutil.copyfileobj(f_tmp, f_points, 1024*1024)
                        f_tmp.close()
                        os.remove(tmp_fn)

                    tmp_fn = data_path + day_files[k][i] + '_users.txt'
                    if os.path.exists(tmp_fn):
                        if f_users is None:
                            f_users = open(data_path + day_files[k][0] + '_users.txt', 'ab+')
                        f_tmp = open(tmp_fn, 'rb')
                        shutil.copyfileobj(f_tmp, f_users, 1024*1024)
                        f_tmp.close()
                        os.remove(tmp_fn)

                    tmp_fn = data_path + day_files[k][i] + '.bin'
                    os.remove(tmp_fn)
                if f_points:
                    f_points.close()
                if f_users:
                    f_users.close()
