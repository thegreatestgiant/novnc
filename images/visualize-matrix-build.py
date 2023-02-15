#!/usr/bin/env python
import time
import sys
import argparse
from PIL import Image
import time
import redis
import os
from urllib.request import urlopen


class VisualizeMatrixBuild(object):
    def __init__(self, *args, **kwargs):
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument("--max-job-x", help="max-job-x", default=8, type=int)
        self.parser.add_argument("--max-job-y", help="max job y", default=4, type=int)
        self.parser.add_argument("--max-x", help="max x pixels", default=32, type=int)
        self.parser.add_argument("--max-y", help="max y pixels", default=16, type=int)
        self.parser.add_argument("--job-x", help="job x", default=1, type=int)
        self.parser.add_argument("--job-y", help="job y", default=1, type=int)
        self.parser.add_argument("--environment", help="redis environment", default="foobar", type=str)
        self.parser.add_argument("--image-file", help="image file location", default="images/static_image.jpg", type=str)
        self.parser.add_argument("--redis-host", help="Redis Host", default="redis-master.redis.svc.cluster.local", type=str)
        self.parser.add_argument("--duration", help="job in milliseconds", default="5000", type=int)
        self.args = self.parser.parse_args()

    def run(self):
        maxX = self.args.max_x
        maxY = self.args.max_y

        pixelsX = int (maxX/self.args.max_job_x)
        pixelsY = int (maxY/self.args.max_job_y)

        offsetX = (self.args.job_x-1) * pixelsX
        offsetY = (self.args.job_y-1) * pixelsY

        numberPixels = pixelsX * pixelsY

        environment = self.args.environment
        duration = self.args.duration

        sleepBetweenPixels = duration / numberPixels

        image_file = self.args.image_file
        if image_file.startswith("http"):
            image = Image.open(urlopen(image_file))
        else:
            image = Image.open(image_file)

        width, height = image.size

        if width != maxX and height != maxY:
            image.thumbnail((maxX, maxY), Image.ANTIALIAS)

        redisClient = redis.Redis(host=self.args.redis_host, port=6379, db=0, password=os.environ.get('REDIS_PASSWORD'), decode_responses=True)

        rgb_im = image.convert('RGB')
        width, height = rgb_im.size

        values = ""
        for y in range(pixelsY):
            for x in range(pixelsX):
                realX=x+offsetX
                realY=y+offsetY
                r, g, b = rgb_im.getpixel((realX%width,realY%height))
                value=("%d,%d,%d,%d,%d")%(realX,realY,r,g,b)
                values+=value
                values+="\n"

            # if there are more than 100 pixels, line by line updates will put too much stress on Redis, updating the entire cell then    
            if (maxX < 100 and maxY < 100):
                    hashKey = ("job/%d/%d/%d") % (self.args.job_x, self.args.job_y, y)
                    redisClient.hset(environment,hashKey,values)
                    values=""
            time.sleep(sleepBetweenPixels*pixelsX/1000)
        hashKey = ("job/%d/%d") % (self.args.job_x, self.args.job_y)
        redisClient.hset(environment,hashKey,values)


# Main function
if __name__ == "__main__":
    stream_pixels = VisualizeMatrixBuild()
    stream_pixels.run()
