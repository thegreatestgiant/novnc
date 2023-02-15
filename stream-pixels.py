#!/usr/bin/env python
from samplebase import SampleBase
import time
import redis
from rgbmatrix import graphics
import os
from PIL import Image
from urllib.request import urlopen

class StreamPixels(SampleBase):
    def __init__(self, *args, **kwargs):
        super(StreamPixels, self).__init__(*args, **kwargs)
        self.parser.add_argument("--max-x", help="max x pixel", default=64, type=int)
        self.parser.add_argument("--max-y", help="max y pixel", default=32, type=int)
        self.parser.add_argument("--environment", help="redis environment", default="foobar", type=str)
        self.parser.add_argument("--sleep-interval", help="sleep interval in milliseconds", default="1000", type=int)
        self.parser.add_argument("--image-file", help="image file location", default="images/github-longer.png", type=str)
        self.parser.add_argument("--redis-host", help="Redis Host", default="redis-master.redis.svc.cluster.local", type=str)

    def run(self):
        maxX = self.args.max_x
        maxY = self.args.max_y
        environment = self.args.environment
        sleepInterval = self.args.sleep_interval

        image_file = self.args.image_file
        if image_file.startswith("http"):
            image = Image.open(urlopen(image_file))
        else:
            image = Image.open(image_file)

        rgb_im = image.convert('RGB')
        width, height = rgb_im.size

        pixelCache = {}
        offscreen_canvas = self.matrix.CreateFrameCanvas()
        redisClient = redis.Redis(host=self.args.redis_host, port=6379, db=0, password=os.environ.get('REDIS_PASSWORD'), decode_responses=True)

        # clear Redis and cache at the beginning
        redisClient.delete(environment)
        for x in range(maxX):
            values = ""
            for y in range(maxY):
                key="%s/%d/%d" % (environment,x,y)
                r, g, b = rgb_im.getpixel((x%width,y%height))
                pixelCache[key]=(r,g,b)

        needScreenUpdate = True
        while True:
            for job, lines in redisClient.hgetall(environment).items():
                for values in lines.split("\n"):
                    if not values:
                        continue
                    x, y, red, green, blue = values.split(",")
                    key=("%s/%s/%s") % (environment,x,y)
                    value=(int(red),int(green),int(blue))
                    cachedValue = pixelCache[key]
                    if (cachedValue != value):
                        needScreenUpdate = True
                        pixelCache[key]=value

                # if job.startswith("reset"):
                # delete everything on redis that has been read, like a message bus
                redisClient.hdel(environment, job)

            if (needScreenUpdate):
                # print("Need to redraw")
                offscreen_canvas.Clear()
                for x in range (maxX):
                    for y in range (maxY):
                        key="%s/%d/%s" % (environment,x,y)
                        red, green, blue = pixelCache[key]
                        offscreen_canvas.SetPixel(x, y, int(red), int(green), int(blue))
                offscreen_canvas = self.matrix.SwapOnVSync(offscreen_canvas)
                needScreenUpdate=False

            time.sleep(sleepInterval/1000)

# Main function
if __name__ == "__main__":
    stream_pixels = StreamPixels()
    if (not stream_pixels.process()):
        stream_pixels.print_help()
