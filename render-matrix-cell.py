#!/usr/bin/env python
import argparse
import time
import os
from urllib.request import urlopen
from urllib.parse import urlparse
from PIL import Image
import pymysql.cursors


class VisualizeMatrixBuild(object):
    def __init__(self, *args, **kwargs):
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument("--max-job-x", help="max-job-x", default=8, type=int)
        self.parser.add_argument("--max-job-y", help="max job y", default=4, type=int)
        self.parser.add_argument("--max-x", help="max x pixels", default=32, type=int)
        self.parser.add_argument("--max-y", help="max y pixels", default=16, type=int)
        self.parser.add_argument("--job-x", help="job x", default=1, type=int)
        self.parser.add_argument("--job-y", help="job y", default=1, type=int)
        self.parser.add_argument("--environment", help="environment", default="barfoo", type=str)
        self.parser.add_argument("--image-file", help="image file location", default="images/static_image.jpg", type=str)
        self.parser.add_argument("--operation", help="operation to use", default=None, type=str)
        self.parser.add_argument("--duration", help="pixel render time in milliseconds", default="3000", type=int)
        self.parser.add_argument("--repetitions", help="times to switch between color and gray", default="0", type=int)
        self.parser.add_argument("--repetition-delay", help="time to wait between repetitions in ms", default="60000", type=int)
        self.parser.add_argument("--connections", help="number of db connections", default="1", type=int)
        self.args = self.parser.parse_args()

    def run(self):
        maxX = self.args.max_x
        maxY = self.args.max_y

        pixelsX = int (maxX/self.args.max_job_x)
        pixelsY = int (maxY/self.args.max_job_y)

        offsetX = (self.args.job_x-1) * pixelsX
        offsetY = (self.args.job_y-1) * pixelsY

        numberPixels = pixelsX * pixelsY

        numberConnections = self.args.connections

        operation = self.args.operation

        environment = self.args.environment
        duration = self.args.duration
        repetitions_delay = self.args.repetition_delay

        repetitions = self.args.repetitions

        sleepBetweenPixels = duration / numberPixels

        image_file = self.args.image_file
        if image_file.startswith("http"):
            image = Image.open(urlopen(image_file))
        else:
            image = Image.open(image_file)

        width, height = image.size

        if width != maxX and height != maxY:
            image.thumbnail((maxX, maxY), Image.ANTIALIAS)


        url = urlparse(os.environ.get('DATABASE_URL'))

        connections = {}
        cursors = {}
        for i in range (numberConnections):
            connections[i]= pymysql.connect(host=url.hostname,
                                        user=url.username,
                                        password=url.password,
                                        db=url.path[1:],
                                        ssl={'ca': 'certs.pem'})
            cursors[i] = connections[i].cursor()
            cursors[i].execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")

        rgb_im = image.convert('RGB')
        width, height = rgb_im.size

        basicSchema = operation == None
        updateWholeCell = numberConnections == 1

        if basicSchema:
            add_pixels = ("INSERT INTO pixel_matrix "
                            "(environment, cell, pixel_data ) "
                            "VALUES (%s, %s, %s)" )
        else:
            add_pixels = ("INSERT INTO pixel_matrix "
                            "(environment, cell, pixel_data, operation ) "
                            "VALUES (%s, %s, %s, %s)" )

        for i in range(repetitions):
            if i != 0:
                time.sleep(repetitions_delay/1000)

            values = ""
            for y in range(pixelsY):
                cursor = cursors[y % numberConnections]
                connection = connections [y % numberConnections]
                for x in range(pixelsX):
                    realX=x+offsetX
                    realY=y+offsetY
                    r, g, b = rgb_im.getpixel((realX%width,realY%height))
                    gray = 0.2989 * r + 0.5870 * g + 0.1140 * b
                    if (i % 2 == 1):
                      r, g, b = gray , gray, gray     
                    value=("%d,%d,%d,%d,%d")%(realX,realY,r,g,b)
                    values+=value
                    values+="\n"
                
                if (not updateWholeCell):
                    hashKey = ("%d/%d/%d") % (self.args.job_x, self.args.job_y, y)
                    if basicSchema:
                        cursor.execute(add_pixels, (environment, hashKey, values))
                    else:
                        cursor.execute(add_pixels, (environment, hashKey, values, operation))
                    connection.commit()
                    values = ""
            
                time.sleep(sleepBetweenPixels*pixelsX/1000)
            
            if updateWholeCell:
                hashKey = ("job/%d/%d") % (self.args.job_x, self.args.job_y)
                if basicSchema:
                        cursor.execute(add_pixels, (environment, hashKey, values))
                else:
                    cursor.execute(add_pixels, (environment, hashKey, values, operation))
                connection.commit()

        for i in range (numberConnections):
            connections[i].close()
            cursors[i].close()

# Main function
if __name__ == "__main__":
    stream_pixels = VisualizeMatrixBuild()
    stream_pixels.run()
