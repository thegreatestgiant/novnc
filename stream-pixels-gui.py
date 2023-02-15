#!/usr/bin/env python
import time
import redis
import os
import PySimpleGUI as sg
import os
from PIL import Image
import io
import argparse

class StreamPixels():
    def __init__(self, *args, **kwargs):
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument("--max-x", help="max x pixel", default=800, type=int)
        self.parser.add_argument("--max-y", help="max y pixel", default=600, type=int)
        self.parser.add_argument("--environment", help="redis environment", default="foobar", type=str)
        self.parser.add_argument("--sleep-interval", help="sleep interval in milliseconds", default="1000", type=int)
        self.parser.add_argument("--redis-port", help="Redis Port", default="6379", type=int)
        self.parser.add_argument("--image-file", help="image file location", default="images/matrix-reset.png", type=str)
        self.parser.add_argument("--redis-host", help="Redis Host", default="redis-master.redis.svc.cluster.local", type=str)
        self.args = self.parser.parse_args()

    def run(self):
        maxX = self.args.max_x
        maxY = self.args.max_y
        environment = self.args.environment
        sleepInterval = self.args.sleep_interval

        image_file = self.args.image_file
        image = Image.open(image_file)

        rgb_im = image.convert('RGB')
        width, height = rgb_im.size

        pixelCache = {}

        redisClient = redis.Redis(host=self.args.redis_host, port=self.args.redis_port, db=0, password=os.environ.get('REDIS_PASSWORD'), decode_responses=True)
        p = redisClient.pipeline(transaction=False)


        # clear Redis and cache at the beginning
        redisClient.delete(environment)
        for x in range(maxX):
            for y in range(maxY):
                key="%s/%d/%d" % (environment,x,y)
                r, g, b = rgb_im.getpixel((x%width,y%height))
                pixelCache[key]=(r,g,b)


        bio = io.BytesIO()
        image.save(bio, format="PNG")
        del image

        layout = [[sg.Graph(
            canvas_size=(maxX, maxY),
            graph_bottom_left=(0, 0),
            graph_top_right=(maxX, maxY),
            key="-GRAPH-",
            change_submits=True,  # mouse click events
            )]
        ]

        sg.SetOptions(element_padding=(0, 0))
        window = sg.Window('Stream-Pixel-Redis', layout, margins=(0,0), size=(maxX, maxY), finalize=True)
        #window = sg.Window('Stream-Pixel-GUI').Layout(layout).Finalize()
        window.Maximize()
        fullScreen = True
        graph = window["-GRAPH-"]
        graph.draw_image(data=bio.getvalue(), location=(0,maxY))

        needScreenUpdate = False

        while True:
            event, values = window.read(timeout=sleepInterval)
            # perform button and keyboard operations
            if event == sg.WIN_CLOSED:
                break

            if event == "-GRAPH-":
                if fullScreen:
                    print("Minimize")
                    window.Normal()
                    fullScreen = False
                else:
                    print("Maxmimize")
                    window.Maximize()
                    fullScreen = True

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
                img = Image.new('RGB', (maxX, maxY))
                for x in range (maxX):
                    for y in range (maxY):
                        key="%s/%d/%s" % (environment,x,y)
                        red, green, blue = pixelCache[key]
                        img.putpixel((x,y), (red,green,blue))
                bio = io.BytesIO()
                img.save(bio, format="PNG")
                graph.draw_image(data=bio.getvalue(), location=(0,maxY))
                window.refresh()
                needScreenUpdate=False
                del img
                print ("updated screen")

# Main function
if __name__ == "__main__":
    stream_pixels = StreamPixels()
    stream_pixels.run()
