from PIL import Image, ImageDraw
import time, pytz, datetime
import json
import math
import gzip
import os, glob

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
borders = [1550, 110, 1772, 362] # right active
#borders = [1308, 767, 1325, 785] # 9
field_size = (2000, 2000)
#out_size = (4096, 2304)
out_size = (1280, 720)
pxl_sz = 0
pxl_diff = (0, 0)
out_path = os.path.expanduser('~/Desktop/data/frames/')
data_path = os.path.expanduser('~/Desktop/data/pxls_space_tmp/')
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
        draw.rectangle((x1, y1, x1+pxl_sz, y1+pxl_sz), fill=color_map[color])

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


if __name__=='__main__':
    files = []
    for file in glob.glob("%s*.bin"%data_path):
        files.append(file)
    files.sort(key=lambda el: os.path.basename(el))
    for f in files:
        print f


    (borders, pxl_sz, pxl_diff) = calc_borders(borders, field_size)
    print pxl_sz, pxl_diff, borders


    img = Image.new('RGBA', out_size, "black")
    #img = Image.open('video_background.png')
    #print img.mode
    #pixels = img.load() # create the pixel map
    ##pixels[x,y] = color_map[col & 0x0f]
    draw = ImageDraw.Draw(img)

    for f in files:
        #dt = '20170410_155244'
        #dt = '20170414_235113'
        #dt = '20170415_144130'
        dt = os.path.splitext(os.path.basename(f))[0]
        tmp = pytz.timezone('Europe/Kiev').localize(datetime.datetime(int(dt[:4]), int(dt[4:6]), int(dt[6:8]), int(dt[9:11]), int(dt[11:13]), int(dt[13:15])))
        tm = int(time.mktime(tmp.timetuple()))

        # read initial image
        y = 0
        f = gzip.open('%s%s.bin'%(data_path, dt))
        for line in read_in_chunks(f, chunk_size=2000):
            for x in range(len(line)):
                #pixels[x,y] = color_map[ord(line[x]) & 0x0f]
                put_pixel(draw, x, y, ord(line[x]) & 0x0f)
            y += 1

        #img.show()
        img.save('%s%d.png'%(out_path, tm))

        with open('%s%s.txt'%(data_path, dt)) as f:
            c = 0
            tm1 = tm
            for line in f:
                c += 1
                #1491828764;1923;1687;3
                tmp = line.split(';')
                if len(tmp) == 4:
                    tm1 = int(tmp[0])
                    x = int(tmp[1])
                    y = int(tmp[2])
                    col = int(tmp[3])
                    #pixels[x,y] = color_map[col & 0x0f]
                    put_pixel(draw, x, y, col & 0x0f)
                else:
                    print 'error at line %d'%c
                    break
                if (tm+10) <= tm1:
                    tm = tm1
                    img.save('%s%d.png'%(out_path, tm))

    del draw


