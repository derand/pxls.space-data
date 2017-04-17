# pxls.space-data

This is two scripts to store pixel data from site pxls.space and create timelapse video from stored data.

Before run scripts install dependencies from 'requirements.txt':

    pip install -r requirements.txt

`history.py` – store history to diretory stored on STORE_PATH environment variable.

`create_frames.py` – create png frames from history stored with `history.py` to timelapse video.

Converting from png-frames to video use ffmpeg like:

    ffmpeg -y -framerate 60 -pattern_type glob -i "frames/*.png" -c:v libx264 -pix_fmt yuv420p -crf 18 -refs 4 -partitions +parti4x4+parti8x8+partp4x4+partp8x8+partb8x8 -subq 12 -trellis 1 -coder 1 -me_range 32 -level 4.1 -profile:v high -bf 12 timelapse.mp4

Font "Data Control" downloaded from [www.1001freefonts.com](http://www.1001freefonts.com/computer-fonts.php).