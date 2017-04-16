from PIL import Image, ImageDraw
import time, pytz, datetime
import json
import math
import gzip
import os, glob, struct, sys

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

# 4096x2304
#borders = [1061, 566, 1720, 1013]
#borders = [0, 0, 2000, 2000]
#borders = [1550, 110, 1772, 362] # right active
#borders = [1308, 767, 1325, 785] # 9
borders = [1751, 24, 1821, 87]
field_size = (2000, 2000)
#out_size = (4096, 2304)
out_size = (1280, 720)
pxl_sz = 0
pxl_diff = (0, 0)
out_path = os.path.expanduser('~/Desktop/data/frames/')
data_path = os.path.expanduser('~/Desktop/data/pxls_space_tmp/')
tm_start = tm_stop = 0
tm_step = 10
'''
    ffmpeg -y -framerate 60 -pattern_type glob -i "/Users/maliy/Desktop/data/frames/*.png" -c:v libx264 -pix_fmt yuv420p -crf 18 -refs 4 -partitions +parti4x4+parti8x8+partp4x4+partp8x8+partb8x8 -subq 12 -trellis 1 -coder 1 -me_range 32 -level 4.1 -profile:v high -bf 12 /Users/maliy/Desktop/out.mp4
'''

def read_in_chunks(file_object, chunk_size=2000):
    while True:
        data = file_object.read(chunk_size)
        if not data:
            break
        yield data

def put_pixel(draw, x, y, color):
    global borders, pxl_sz, pxl_diff, color_map
    if x >= borders[0] and x <= borders[2] and y >= borders[1] and y <= borders[3] and color < len(color_map):
        x1, y1 = (x - borders[0]) * pxl_sz + pxl_diff[0], (y - borders[1]) * pxl_sz + pxl_diff[1]
        if pxl_sz > 1:
            draw.rectangle((x1, y1, x1+pxl_sz-1, y1+pxl_sz-1), fill=color_map[color])
        else:
            draw.point((x1, y1), fill=color_map[color])

def calc_borders(borders, field_size):
    global out_size
    w = borders[2]-borders[0]
    h = borders[3]-borders[1]
    pxl_sz = 0
    if float(w)/float(h) > float(out_size[0])/float(out_size[1]):
        # weight
        h = int(w * float(out_size[1]) / float(out_size[0]))
        pxl_sz = out_size[0] / w
    else:
        # height
        w = int(h * float(out_size[0])/float(out_size[1]))
        pxl_sz = out_size[1] / h
    center = (borders[2]+borders[0])/2, (borders[3]+borders[1])/2
    '''
    pxl_diff = ( -(out_size[0]%pxl_sz)/2, -(out_size[1]%pxl_sz)/2 )
    if pxl_diff[0] != 0:
        w += 2
    if pxl_diff[1] != 0:
        h += 2
    
    borders[0], borders[1] = center[0]-w/2, center[1]-h/2
    borders[2], borders[3] = borders[0]+w, borders[1]+h
    '''
    tmp = (int(math.ceil(float(out_size[0])/(2*pxl_sz))), int(math.ceil(float(out_size[1])/(2*pxl_sz))))
    borders[0], borders[1] = center[0]-tmp[0], center[1]-tmp[1]
    borders[2], borders[3] = center[0]+tmp[0], center[1]+tmp[1]
    if borders[0] < 0:
        borders[0] = 0
    if borders[1] < 0:
        borders[1] = 0
    if borders[2] > field_size[0]:
        borders[2] = field_size[0]
    if borders[3] > field_size[1]:
        borders[3] = field_size[1]
    pxl_diff = ((out_size[0]-(borders[2]-borders[0])*pxl_sz)/2, (out_size[1]-(borders[3]-borders[1])*pxl_sz)/2)
    return (borders, pxl_sz, pxl_diff)

def file_time(fn):
    dt = os.path.splitext(os.path.basename(fn))[0]
    tmp = pytz.timezone('Europe/Kiev').localize(datetime.datetime(int(dt[:4]), int(dt[4:6]), int(dt[6:8]), int(dt[9:11]), int(dt[11:13]), int(dt[13:15])))
    return int(time.mktime(tmp.timetuple()))

def clear_files(files, tm_start, tm_stop):
    while len(files) > 1:
        tm = file_time(files[1])
        if tm > tm_start:
            break
        files = files[1:]
    return files

def fill_frame(filename, draw):
    global field_size
    isize = 0
    with open(filename, 'rb') as f:
        f.seek(-4, 2)
        isize = struct.unpack('I', f.read(4))[0]
    if isize != field_size[0] * field_size[1]:
        return False

    clear_frame(draw)
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
    #img.show()
    img.save(filename)

if __name__=='__main__':
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

    (borders, pxl_sz, pxl_diff) = calc_borders(borders, field_size)
    print pxl_sz, pxl_diff, borders


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
    f_points_counter = 0
    sys.stdout.write('%s: %d'%(dt, tm_next_frame))
    sys.stdout.flush()
    while True:
        while tm >= tm_next_frame:
            save_frame(img, '%s%d.png'%(out_path, tm_next_frame))
            tm_next_frame += tm_step
            if tm_next_frame > tm_stop:
                break
            data_frame = False
            sys.stdout.write('\r%s: %d'%(dt, tm_next_frame))
            sys.stdout.flush()

        line = f_points.readline()
        f_points_counter += 1
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
            else:
                print 'error at line %d'%c
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
                sys.stdout.write('\r%s: %d'%(dt, tm_next_frame))
                sys.stdout.flush()
            data_frame = fill_frame(filename='%s%s.bin'%(data_path, dt), draw=draw)
            f_points.close()
            f_points = open('%s%s.txt'%(data_path, dt))
            f_points_counter = 0
    del draw
    print


