#!/usr/bin/env python
import argparse
import constants
import os
import io
from urllib.parse import urlparse
import PySimpleGUI as sg
from PIL import Image
import pymysql.cursors


class StreamPixels():
    def __init__(self, *args, **kwargs):
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument("--max-x", help="max x pixel", default=800, type=int)
        self.parser.add_argument("--max-y", help="max y pixel", default=600, type=int)
        self.parser.add_argument("--environment", help="redis environment", default="foobar", type=str)
        self.parser.add_argument("--sleep-interval", help="sleep interval in milliseconds", default="1000", type=int)
        self.parser.add_argument("--image-file", help="image file location", default="images/matrix-start.png", type=str)
        self.args = self.parser.parse_args()

    def run(self):
        maxX = self.args.max_x
        maxY = self.args.max_y
        environment = self.args.environment
        

        image_file = self.args.image_file
        image = Image.open(image_file)

        rgb_im = image.convert('RGB')
        width, height = rgb_im.size

        pixelCache = {}
        operationCache = {}
        sleepInterval = self.args.sleep_interval

        url = urlparse(os.environ.get('DATABASE_URL'))


        # connect to MySQL with TLS enabled
        connection = pymysql.connect(host=url.hostname,
                                        user=url.username,
                                        password=url.password,
                                        db=url.path[1:],
                                        ssl={'ca': 'certs.pem'})

        #connection = pymysql.connect(user=url.username,password=url.password, host=url.hostname,port=url.port, database=url.path[1:], clieent)
        cursor = connection.cursor()
        cursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")
        
        # clear Vitess and cache at the beginning
        clear_environment=("delete from pixel_matrix where environment = %s limit 99999")
        cursor.execute(clear_environment, environment)
        connection.commit()

        for x in range(maxX):
            for y in range(maxY):
                key="%s/%d/%d" % (environment,x,y)
                r, g, b = rgb_im.getpixel((x%width,y%height))
                pixelCache[key]=(r,g,b)
                operationCache[key] = None


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
        menu = ['&Right', ['Use advanced schema', 'Use basic schema']]
        window = sg.Window('Stream-Pixel-PS', layout, margins=(0,0), size=(maxX, maxY), right_click_menu=menu, finalize=True)
        
        #window = sg.Window('Stream-Pixel-GUI').Layout(layout).Finalize()
        window.Maximize()
        fullScreen = True
        graph = window["-GRAPH-"]
        graph.draw_image(data=bio.getvalue(), location=(0,maxY))

        needScreenUpdate = False
        useAdvancedSchema = False

        id = 0
        while True:
            event, values = window.read(timeout=sleepInterval)
            # perform button and keyboard operations
            if event == sg.WIN_CLOSED:
                break

            elif event == "-GRAPH-":
                if fullScreen:
                    print("Minimize")
                    window.Normal()
                    fullScreen = False
                else:
                    print("Maxmimize")
                    window.Maximize()
                    fullScreen = True
            elif event == "Use advanced schema":
                print ("Switch to advanced schema")
                useAdvancedSchema = True
            elif event == "Use basic schema":
                print ("Switch back to basic schema")
                useAdvancedSchema = False

            if useAdvancedSchema == False:
                line_query = ("select id, cell, pixel_data from pixel_matrix where environment = %s and id > %s order by ID LIMIT 500")
            else:
                line_query = ("select id, cell, pixel_data, operation from pixel_matrix where environment = %s and id > %s order by ID LIMIT 500")

            cursor.execute(line_query, (environment, id))
            rows=cursor.fetchall()
            
            #for (id, cell, pixel_data) in rows:
            for row in rows:
                operation = None
                if useAdvancedSchema:
                    (id, cell, pixel_data, operation) = row
                else:
                    (id, cell, pixel_data) = row
                for values in pixel_data.split("\n"):
                    if not values:
                        continue
                    x, y, red, green, blue = values.split(",")
                    key=("%s/%s/%s") % (environment,x,y)

                    cachedOperation = operationCache[key]
                    if cachedOperation == constants.PIN:
                        # if a pinned pixel should be replaced, the PIN operation has to be used
                        if operation != constants.PIN:
                            continue
                    
                    if operation != cachedOperation:
                        operationCache[key] = operation

                    value=(int(red),int(green),int(blue))
                    cachedValue = pixelCache[key]
                    if (cachedValue != value):
                        needScreenUpdate = True
                        pixelCache[key]=value
                    


                #clear_environment = ("delete from pixel_matrix where environment = %s and cell= %s")
                #cursor.execute(clear_environment, (environment, cell))

            connection.commit()

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
