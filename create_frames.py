#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PIL import Image, ImageDraw, ImageFont
import time, pytz, datetime
import json
import math
import gzip
import os, glob, struct, sys
import argparse

color_map = (
        (0xff, 0xff, 0xff, 0xff),
        (0xe4, 0xe4, 0xe4, 0xff),
        (0x88, 0x88, 0x88, 0xff),
        (0x22, 0x22, 0x22, 0xff),
        (0xfd, 0xa7, 0xd0, 0xff),
        (0xe2, 0x0e, 0x15, 0xff),
        (0xe3, 0x96, 0x29, 0xff),
        (0x9f, 0x6b, 0x46, 0xff),
        (0xe4, 0xda, 0x39, 0xff),
        (0x97, 0xe1, 0x56, 0xff),
        (0x20, 0xbe, 0x2c, 0xff),
        (0x27, 0xd2, 0xdc, 0xff),
        (0x16, 0x82, 0xc4, 0xff),
        (0x0a, 0x00, 0xe4, 0xff),
        (0xcd, 0x6d, 0xe0, 0xff),
        (0x80, 0x00, 0x7d, 0xff),
    )

pxl_sz = 0
pxl_diff = (0, 0)
tm = tm_next_frame = 0
pixel_counter = 0
pixel_counter_last = 0
pixel_counter_arr = []
dt = None
frame_counter = 0
s1 = s2 = s3 = ''
users = None
users_next = (0, 0)

store_rect = field_size = out_size = None
out_path = data_path = None
tm_start = tm_stop = tm_step = 0

# statistic
stat_hide = stat_fontsize = stat_rect_padding = stat_font = None
stat_text_update = 60
stat_accumulation = 0

data_frame = True
frame_miss_counter = 0

my_timezone = 'Europe/Kiev'


def read_in_chunks(file_object, chunk_size=2000):
    while True:
        data = file_object.read(chunk_size)
        if not data:
            break
        yield data

def put_pixel(draw, x, y, color):
    global store_rect, pxl_sz, pxl_diff, color_map
    if x >= store_rect[0] and x <= store_rect[2] and y >= store_rect[1] and y <= store_rect[3] and color < len(color_map):
        x1, y1 = (x - store_rect[0]) * pxl_sz + pxl_diff[0], (y - store_rect[1]) * pxl_sz + pxl_diff[1]
        if pxl_sz > 1:
            draw.rectangle((x1, y1, x1+pxl_sz-1, y1+pxl_sz-1), fill=color_map[color])
        else:
            draw.point((x1, y1), fill=color_map[color])

def calc_storerect(store_rect, field_size):
    global out_size
    w = store_rect[2]-store_rect[0]
    h = store_rect[3]-store_rect[1]
    pxl_sz = 0
    if float(w)/float(h) > float(out_size[0])/float(out_size[1]):
        # weight
        h = int(w * float(out_size[1]) / float(out_size[0]))
        pxl_sz = out_size[0] // w
    else:
        # height
        w = int(h * float(out_size[0])/float(out_size[1]))
        pxl_sz = out_size[1] // h
    center = (store_rect[2]+store_rect[0])//2, (store_rect[3]+store_rect[1])//2

    tmp = (int(math.ceil(float(out_size[0])/(2*pxl_sz))), int(math.ceil(float(out_size[1])/(2*pxl_sz))))
    store_rect[0], store_rect[1] = center[0]-tmp[0], center[1]-tmp[1]
    store_rect[2], store_rect[3] = center[0]+tmp[0], center[1]+tmp[1]
    if store_rect[0] < 0:
        store_rect[0] = 0
    if store_rect[1] < 0:
        store_rect[1] = 0
    if store_rect[2] > field_size[0]:
        store_rect[2] = field_size[0]
    if store_rect[3] > field_size[1]:
        store_rect[3] = field_size[1]
    pxl_diff = ((out_size[0]-(store_rect[2]-store_rect[0])*pxl_sz)//2, (out_size[1]-(store_rect[3]-store_rect[1])*pxl_sz)//2)
    return (store_rect, pxl_sz, pxl_diff)

def file_time(fn):
    global my_timezone
    dt = os.path.splitext(os.path.basename(fn))[0]
    tmp = pytz.timezone(my_timezone).localize(datetime.datetime(int(dt[:4]), int(dt[4:6]), int(dt[6:8]), int(dt[9:11]), int(dt[11:13]), int(dt[13:15])))
    return int(time.mktime(tmp.timetuple()))

def clear_files(files, tm_start, tm_stop):
    while len(files) > 1:
        tm = file_time(files[1])
        if tm > tm_start:
            break
        files = files[1:]
    while len(files) > 1:
        tm = file_time(files[-1])
        if tm < tm_stop:
            break
        files = files[:-1]
    return files

def fill_frame(filename, draw):
    global field_size
    isize = 0
    with open(filename, 'rb') as f:
        f.seek(-4, 2)
        isize = struct.unpack('I', f.read(4))[0]
    if isize != field_size[0] * field_size[1]:
        return False

    y = 0
    f = gzip.open(filename)
    for line in read_in_chunks(f, chunk_size=2000):
        for x in range(len(line)):
            #pixels[x,y] = color_map[ord(line[x]) & 0x0f]
            put_pixel(draw, x, y, ord(line[x]) & 0x0f)
        y += 1
    return True

def clear_frame(draw):
    draw.rectangle((0, 0, out_size[0], out_size[1]), fill=(0xff, 0xff, 0xff, 0xff))

def save_frame(img, filename):
    global tm_next_frame
    global pixel_counter, pixel_counter_last, pixel_counter_arr
    global dt, frame_counter
    global s2, s3
    global users
    global stat_hide, stat_rect_padding, stat_fontsize, stat_font, stat_text_update, stat_accumulation
    global data_frame, frame_miss_counter
    #img.show()

    pixel_diff = pixel_counter - pixel_counter_last
    pixel_counter_arr.append(pixel_diff)
    if len(pixel_counter_arr) > stat_text_update:
        pixel_counter_arr.pop(0)
    pixel_diff = float(sum(pixel_counter_arr)) / (len(pixel_counter_arr) * tm_step)
    pixel_counter_last = pixel_counter

    s1 = time.strftime("%a, %d %b %Y %H:%M", time.localtime(tm_next_frame))
    if frame_counter % stat_text_update == 1:
        s2 = '%.0f pxls/s'%pixel_diff
    if frame_counter % stat_text_update == 1 or s3 == '':
        if users is not None:
            s3 = 'Users: %d'%users[0]
        else:
            s3 = ''

    if stat_accumulation > 0:
        stat_accumulation -= 1
        sys.stdout.write('\r%s(%d) -%d: %s   %d/%d/%s   %s'%(dt, tm_next_frame, stat_accumulation, s1, pixel_counter_arr[-1]//tm_step, sum(pixel_counter_arr)//(len(pixel_counter_arr)*tm_step), s2, s3))
        sys.stdout.flush()
        return

    _s3 = s3
    if frame_miss_counter > 5:
        _s3 = '-'

    if not data_frame:
        frame_miss_counter += 1
    else:
        frame_miss_counter = 0
    frame_counter += 1

    sys.stdout.write('\r%s(%d) %d: %s   %d/%d/%s   %s'%(dt, tm_next_frame, frame_counter, s1, pixel_counter_arr[-1]//tm_step, sum(pixel_counter_arr)//(len(pixel_counter_arr)*tm_step), s2, _s3))
    sys.stdout.flush()

    if stat_hide:
        img.save(filename, 'PNG')
    else:
        tmp = Image.new('RGBA', out_size)
        d = ImageDraw.Draw(tmp)
        d.rectangle((2*stat_rect_padding, out_size[1]-stat_fontsize-5*stat_rect_padding, out_size[0]-2*stat_rect_padding, out_size[1]-2*stat_rect_padding), fill=(0x00, 0x00, 0x00, 0x80))
        d.text((3*stat_rect_padding, out_size[1]-stat_fontsize-4*stat_rect_padding), s1, font=stat_font, fill=(0xff, 0xff, 0xff, 0xa0))
        d.text((out_size[0]//4, out_size[1]-stat_fontsize-4*stat_rect_padding), s2, font=stat_font, fill=(0xff, 0xff, 0xff, 0xa0))
        d.text((3*out_size[0]//8, out_size[1]-stat_fontsize-4*stat_rect_padding), _s3, font=stat_font, fill=(0xff, 0xff, 0xff, 0xa0))
        Image.alpha_composite(img, tmp).save(filename, 'PNG')
        del d

def check_users(f_users):
    global users, users_next, tm
    if tm > users_next[1] or users is None:
        line = f_users.readline()
        if line:
            tmp = line.split(';')
            if len(tmp) == 2:
                users = users_next
                users_next = (int(tmp[1]), int(tmp[0]))


if __name__=='__main__':
    script_path = os.path.dirname(os.path.realpath(__file__))
    os.chdir(script_path)

    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--store_rect',    type=str, default='0:0:2000:2000', help="field rectangle to store x1:y1:x2:y2 (default: 0:0:2000:2000)")
    parser.add_argument('-f', '--field_size', type=str, default='2000:2000', help="filed size width:height (default: 2000:2000)")
    parser.add_argument('-s', '--out_size',   type=str, default='4096:2304', help="out images size width:height (default: 4096:2304)")
    parser.add_argument('-o', '--out_path',   type=str, default='/mnt/', help="out dir to store images (default: /mnt/)")
    parser.add_argument('-d', '--data_path',  type=str, default='/mnt/', help="source data path (default: /mnt/)")
    parser.add_argument('--time_start',       type=int, default=0, help="start time in unixtime format")
    parser.add_argument('--time_stop',        type=int, default=0, help="stop time in unixtime format")
    parser.add_argument('--time_step',        type=int, default=10, help="step in seconds between frames (default: 10)")
    parser.add_argument('--stat_hide',        action='store_true', help="show statistic")
    parser.add_argument('--stat_fontsize',    type=int, default=-1, help="font size for statistic")
    parser.add_argument('--stat_fontfile',    type=str, default='data-latin.ttf', help="font file for statistic")
    parser.add_argument('--stat_rect_padding',type=int, default=-1, help="rect padding for statistic")
    parser.add_argument('--stat_text_update', type=int, default=60, help="update text every X frames")
    args = parser.parse_args()

    store_rect = map(int, args.store_rect.split(':'))[0:4]
    field_size = map(int, args.field_size.split(':'))[0:2]
    out_size = map(int, args.out_size.split(':'))[0:2]

    out_path = args.out_path
    data_path = args.data_path

    tm_start = args.time_start
    tm_stop = args.time_stop
    tm_step = args.time_step
    tm = tm_next_frame = tm_start

    stat_hide = args.stat_hide
    if args.stat_fontsize < 0:
        stat_fontsize = out_size[1] // 30
    if args.stat_rect_padding < 0:
        stat_rect_padding = stat_fontsize // 4
    stat_font = ImageFont.truetype('data-latin.ttf', stat_fontsize)
    stat_text_update = args.stat_text_update

    if tm_start > 0:
        stat_accumulation = stat_text_update + 1
        tm_start -= (stat_text_update + 1) * tm_step


    if tm_stop <= tm_start:
        tm_stop = int(time.time())

    files = []
    for file in glob.glob("%s*.bin"%data_path):
        files.append(file)
    files.sort(key=lambda el: os.path.basename(el))
    files = clear_files(files, tm_start, tm_stop)
    for f in files:
        print f

    if len(files) == 0:
        print 'No match files'
        exit()

    (store_rect, pxl_sz, pxl_diff) = calc_storerect(store_rect, field_size)
    print pxl_sz, pxl_diff, store_rect


    img = Image.new('RGBA', out_size, "black")
    #img = Image.open('video_background.png')
    #print img.mode
    #pixels = img.load() # create the pixel map
    ##pixels[x,y] = color_map[col & 0x0f]
    draw = ImageDraw.Draw(img)

    tm_file = file_time(files[0])
    tm = max(tm_file, tm_start)
    tm_next_frame = tm
    filename = files.pop(0)
    dt = os.path.splitext(os.path.basename(filename))[0]
    tm_file = file_time(filename)

    # read initial image
    data_frame = fill_frame(filename='%s%s.bin'%(data_path, dt), draw=draw)
    f_points = open('%s%s.txt'%(data_path, dt))
    f_points_line_counter = 0
    tmp_fn = '%s%s_users.txt'%(data_path, dt)
    if os.path.exists(tmp_fn):
        f_users = open(tmp_fn)
        check_users(f_users)
    else:
        users = None
        f_users = None
    while True:
        while tm >= tm_next_frame:
            save_frame(img, '%s%d.png'%(out_path, tm_next_frame))
            tm_next_frame += tm_step
            if tm_next_frame > tm_stop:
                break
            data_frame = False

        line = f_points.readline()
        f_points_line_counter += 1
        pixel_counter += 1
        if line:
            tmp = line.split(';')
            if len(tmp) == 4:
                data_frame = True
                tm = int(tmp[0])
                x = int(tmp[1])
                y = int(tmp[2])
                col = int(tmp[3])
                #pixels[x,y] = color_map[col & 0x0f]
                put_pixel(draw, x, y, col & 0x0f)
                if f_users:
                    check_users(f_users)
            else:
                print '\nError at line %d, file: %s'%(f_points_line_counter, dt)
                break
        else:
            if len(files) == 0:
                break
            filename = files.pop(0)
            dt = os.path.splitext(os.path.basename(filename))[0]
            tm = file_time(filename)
            data_frame = False
            while tm >= tm_next_frame:
                save_frame(img, '%s%d.png'%(out_path, tm_next_frame))
                tm_next_frame += tm_step
                if tm_next_frame > tm_stop:
                    break
            data_frame = fill_frame(filename='%s%s.bin'%(data_path, dt), draw=draw)
            f_points.close()
            f_points = open('%s%s.txt'%(data_path, dt))
            f_points_line_counter = 0
            if f_users:
                f_users.close()
            tmp_fn = '%s%s_users.txt'%(data_path, dt)
            if os.path.exists(tmp_fn):
                f_users = open(tmp_fn)
                check_users(f_users)
            else:
                users = None
                f_users = None
    del draw
    print


