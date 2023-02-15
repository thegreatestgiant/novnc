#!/usr/bin/env python
from samplebase import SampleBase
import time
import subprocess
from rgbmatrix import graphics

class Pod:
     def __init__(self, name, status, node, position):
         self.name = name
         self.status = status
         self.node = node
         self.position = position


class PodStatusLed(SampleBase):
    def __init__(self, *args, **kwargs):
        super(PodStatusLed, self).__init__(*args, **kwargs)
        self.parser.add_argument("-n", "--namespace", help="Kubernetes namespace", default="github-actions-runner-link")
        self.parser.add_argument("--length", help="pixel length", default=8, type=int)
        self.parser.add_argument("--height", help="pixel height", default=8, type=int)
        self.parser.add_argument("nodes", action='store', nargs='+', default=["node64-1", "node64-2"])

    def find_first_unused_position (positionSet):
        for i in range (1000):
            if (not i in positionSet):
                 return i
        return -1

    def status_color(status):
      return {
            'Running': 'green',
            'CrashLoopBackOff': 'red',
            'ImagePullBackOff': 'red',
            'InvalidImageName': 'red',
            'Terminating': 'brown',
            'Completed': 'blue',
            'Pending': 'white',
            'ContainerCreating': 'yellow',
            'Terminated': 'black',
        }.get(status, 'pink')

    def status_color_led(status):
      return {
            'Running': graphics.Color(0, 255, 0),
            'CrashLoopBackOff': graphics.Color(255, 0, 0),
            'CreateContainerError': graphics.Color(255, 0, 0),
            'InvalidImageName': graphics.Color(255, 0, 0),
            'ImagePullBackOff': graphics.Color(255, 0, 0),
            'Terminating': graphics.Color(165,42,42),
            'Completed': graphics.Color(0, 0, 255),
            'Pending': graphics.Color(255, 255, 255),
            'ContainerCreating': graphics.Color(255, 255, 0),
            'Terminated': graphics.Color(0, 0, 0),
            'Ready': graphics.Color(128, 128, 128),
            'NotReady': graphics.Color(255, 0, 0)
        }.get(status, graphics.Color(255,182,193))

    def run(self):
        nodes = {}
        nodeStatus = {}
        nodesByPosition = {}
        positionsAlreadyTaken = {}

        for node in self.args.nodes:
            nodes[node] = {}
            nodeStatus[node] = "NotReady"
            nodesByPosition[node] = []
            positionsAlreadyTaken[node] = set()


        # 64 / #(number nodes)
        maxX = int(64/len(self.args.nodes))
        maxY = 32

        podPixelLength=self.args.length
        podPixelHeight=self.args.height
        positionMax = int(maxX/podPixelLength)*int(maxY/podPixelHeight)

        offscreen_canvas = self.matrix.CreateFrameCanvas()

        while True:
            offscreen_canvas.Clear()
            podsSeenThisRound = set()
            podsToBeInsertedThisRound = {}
            for node in self.args.nodes:
                podsToBeInsertedThisRound[node]= []

            output = subprocess.getoutput("kubectl get nodes --no-headers")
            for row in output.split("\n"):
                values = row.split();
                if (not values):
                    continue
                # read in node status
                nodeStatus[values[0]]=values[1]

            output = subprocess.getoutput("kubectl get pods --namespace %s --no-headers -o wide" % self.args.namespace)
            for row in output.split("\n"):
                values = row.split();
                if (not values):
                    continue

                podStatus = values[2]
                nodeName = values[6]
                podName = values[0] + "-" + nodeName

                if (nodeName not in nodes.keys()):
                    print ("Node %s not displayed on LED matrix, ignoring pod %s" % (nodeName, podName))
                    continue

                podsSeenThisRound.add(podName)

                pod = nodes[nodeName].get(podName)
                if (not pod):
                    # we have to schedule the position after this loop
                    podsToBeInsertedThisRound[nodeName].append(Pod(podName, podStatus, nodeName, -1))
                else:
                    # we only change the status, and maybe node position is already set
                    pod.status=podStatus


            for node, pods in podsToBeInsertedThisRound.items():
                performedDefrag = False
                for pod in pods:
                    position = PodStatusLed.find_first_unused_position(positionsAlreadyTaken[pod.node])
                    if position >= positionMax:
                        if not performedDefrag:
                            # idea: turn defrag logic into a function
                            for podName, existingPod in nodes[pod.node].items():
                                if (not podName in podsSeenThisRound):
                                    # mark position for potential override, don't do it yet
                                    positionsAlreadyTaken[existingPod.node].remove(existingPod.position)
                            performedDefrag = True
                            position = PodStatusLed.find_first_unused_position(positionsAlreadyTaken[pod.node])

                    # if defrag was already performed this round or we have not been lucky
                    if position >= positionMax:
                        print("LED Matrix too small, skipping node %s until we can allocate a position." % pod.name)
                        continue

                    pod.position = position
                    positionsAlreadyTaken[pod.node].add(position)
                    nodes[pod.node][pod.name] = pod
                    if (position<len(nodesByPosition[pod.node])):
                        previousPod = nodesByPosition[pod.node][pod.position]
                        nodes[previousPod.node].pop(previousPod.name)
                        nodesByPosition[pod.node][pod.position]=pod
                    else:
                        nodesByPosition[pod.node].append(pod)

            offsetX = 0
            for node, pods in nodesByPosition.items():
                i = 0
                borderColor=PodStatusLed.status_color_led(nodeStatus[node])
                # draw boundaries between nodes
                for y in range (maxY):
                    offscreen_canvas.SetPixel(offsetX, y, borderColor.red, borderColor.green, borderColor.blue)
                    offscreen_canvas.SetPixel(offsetX + maxX - 1, y, borderColor.red, borderColor.green, borderColor.blue)

                for pod in pods:
                    if (not pod.name in podsSeenThisRound):
                        pod.status="Terminated"
                    print("Pod: %s, Status: %s, Node: %s, Color: %s, Position: %i" % (pod.name, pod.status, pod.node, PodStatusLed.status_color(pod.status), pod.position))
                    basePosX = (i * podPixelLength) % maxX
                    basePosY = (int) (i*podPixelLength/maxX) * podPixelHeight
                    for x in range (podPixelLength):
                        for y in range (podPixelHeight):
                            # print("x: %d, y: %d, color: %s" % (basePosX + offsetX + x, basePosY + y, PodStatusLed.status_color(pod.status)))
                            color = PodStatusLed.status_color_led(pod.status)
                            # draw frame
                            if (x == 0 or y == 0 or x == podPixelLength-1 or y == podPixelHeight-1):
                                color = borderColor
                            # self.matrix.SetPixel(basePosX + offsetX + x, basePosY + y, color.red, color.green, color.blue)
                            offscreen_canvas.SetPixel(basePosX + offsetX + x, basePosY + y, color.red, color.green, color.blue)
                    i+=1
                offsetX += maxX

            offscreen_canvas = self.matrix.SwapOnVSync(offscreen_canvas)
            time.sleep(1)


# Main function
if __name__ == "__main__":
    pod_status_led = PodStatusLed()
    if (not pod_status_led.process()):
        pod_status_led.print_help()
