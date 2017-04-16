from PIL import Image
import time, pytz, datetime
import json

color_map = (
        (0xff, 0xff, 0xff),
        (0xe4, 0xe4, 0xe4),
        (0x88, 0x88, 0x88),
        (0x22, 0x22, 0x22),
        (0xfd, 0xa7, 0xd0),
        (0xe2, 0x0e, 0x15),
        (0xe3, 0x96, 0x29),
        (0x9f, 0x6b, 0x46),
        (0xe4, 0xda, 0x39),
        (0x97, 0xe1, 0x56),
        (0x20, 0xbe, 0x2c),
        (0x27, 0xd2, 0xdc),
        (0x16, 0x82, 0xc4),
        (0x0a, 0x00, 0xe4),
        (0xcd, 0x6d, 0xe0),
        (0x80, 0x00, 0x7d),
    )

def read_in_chunks(file_object, chunk_size=2000):
    while True:
        data = file_object.read(chunk_size)
        if not data:
            break
        yield data


if __name__=='__main__':
    dt = '20170410_155244'
    out_path = '/Users/maliy/Desktop/data/'
    # 4096x2304
    borders = (1061, 566, 1720, 1013)

    tmp = pytz.timezone('Europe/Kiev').localize(datetime.datetime(int(dt[:4]), int(dt[4:6]), int(dt[6:8]), int(dt[9:11]), int(dt[11:13]), int(dt[13:15])))
    tm = int(time.mktime(tmp.timetuple()))

    img = Image.new( 'RGB', (2000, 2000), "white") 
    pixels = img.load() # create the pixel map

    # read initial image
    y = 0
    f = open('%s.bin'%dt)
    for line in read_in_chunks(f, chunk_size=2000):
        for x in range(len(line)):
            pixels[x,y] = color_map[ord(line[x]) & 0x0f]
        y += 1

    #img.show()
    img.save('%s%d.png'%(out_path, tm))

    with open('%s.txt'%dt) as f:
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
                pixels[x,y] = color_map[col & 0x0f]
            else:
                print 'error at line %d'%c
                break
            if (tm+10) <= tm1:
                tm = tm1
                img.save('%s%d.png'%(out_path, tm))

