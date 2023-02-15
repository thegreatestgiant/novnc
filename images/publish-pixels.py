#!/usr/bin/env python
import time
import sys
import argparse
from PIL import Image
import time
import redis
import os
from urllib.request import urlopen


class StreamPixels(object):
    def __init__(self, *args, **kwargs):
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument("--max-x", help="max x pixel", default=16, type=int)
        self.parser.add_argument("--job-x", help="job x", default=0, type=int)
        self.parser.add_argument("--max-y", help="max y pixel", default=16, type=int)
        self.parser.add_argument("--job-y", help="job y", default=0, type=int)
        self.parser.add_argument("--environment", help="redis environment", default="foobar", type=str)
        self.parser.add_argument("--image-file", help="image file location", default="images/static_image.jpg", type=str)
        self.parser.add_argument("--redis-host", help="Redis Host", default="redis-master.redis.svc.cluster.local", type=str)
        self.parser.add_argument("--sleep-interval", help="sleep interval in milliseconds", default="0", type=int)
        self.args = self.parser.parse_args()

    def run(self):
        maxX = self.args.max_x
        maxY = self.args.max_y
        offsetX = self.args.job_x * maxX
        offsetY = self.args.job_y * maxY

        environment = self.args.environment
        sleepInterval = self.args.sleep_interval

        image_file = self.args.image_file
        if image_file.startswith("http"):
            image = Image.open(urlopen(image_file))
        else:
            image = Image.open(image_file)

        width, height = image.size
        if width != maxX and height != maxY:
            image.thumbnail((maxX, maxY), Image.ANTIALIAS)

        redisClient = redis.Redis(host=self.args.redis_host, port=6379, db=0, password=os.environ.get('REDIS_PASSWORD'), decode_responses=True)
        p = redisClient.pipeline(transaction=False)


        rgb_im = image.convert('RGB')
        width, height = rgb_im.size

        # clear screen
        redisClient.delete(environment)

        values = ""
        for x in range(maxX):
            values=""
            for y in range(maxY):

                r, g, b = rgb_im.getpixel((x%width, y%height))
                value=("%d,%d,%d,%d,%d")%(x+offsetX,y + offsetY,r,g,b)
                values+=value
                values+="\n"
                # print("Setting key %s with value %s" % (key, value))
                # p.set(key,value)
            redisClient.hset(environment,("line%d") % (x), values)
        # p.execute()
        #redisClient.hset(environment,"reset",values)

        #time.sleep(sleepInterval/1000)

# Main function
if __name__ == "__main__":
    stream_pixels = StreamPixels()
    stream_pixels.run()
