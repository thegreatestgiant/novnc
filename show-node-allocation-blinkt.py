#!/usr/bin/env python
import time
import argparse
import blinkt
import subprocess

class Pod:
     def __init__(self, name, status, node, position, shortName):
         self.name = name
         self.status = status
         self.node = node
         self.position = position
         self.shortName = shortName


class PodStatusLed():
    def __init__(self, *args, **kwargs):
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument("--max-y", help="max y pixels", default=blinkt.NUM_PIXELS, type=int)
        self.parser.add_argument("-n", "--namespace", help="Kubernetes namespace", default="github-actions-runner-link")
        self.parser.add_argument("nodes", action='store', nargs='+', default=["node64-2"])

        self.args = self.parser.parse_args()

    def find_first_unused_position (positionSet):
        for i in range (1000):
            if (not i in positionSet):
                 return i
        return -1

    def status_color(status):
      return {
            'Running': [0, 255, 0],
            'CrashLoopBackOff': [255, 0, 0],
            'CreateContainerError': [255, 0, 0],
            'InvalidImageName': [255, 0, 0],
            'ImagePullBackOff': [255, 0, 0],
            'Terminating': [165,42,42],
            'Completed': [0, 0, 255],
            'Pending': [255, 255, 255],
            'ContainerCreating': [255, 255, 0],
            'Terminated': [0, 0, 0],
            'Ready': [128, 128, 128],
            'NotReady': [255, 0, 0]
        }.get(status, [255,182,193])


    def run(self):
        nodes = {}
        nodeStatus = {}
        nodesByPosition = {}
        positionsAlreadyTaken = {}
        positionMax = self.args.max_y

        numberNodes=len(self.args.nodes)
        namespace = self.args.namespace


        for node in self.args.nodes:
            nodes[node] = {}
            nodeStatus[node] = "NotReady"
            nodesByPosition[node] = []
            positionsAlreadyTaken[node] = set()

        while True:

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

            output = subprocess.getoutput("kubectl get pods --namespace %s --no-headers -o wide" % namespace)
            for row in output.split("\n"):
                values = row.split();
                if (not values):
                    continue

                podStatus = values[2]
                nodeName = values[6]
                podShortName = values[0]
                podName = podShortName + "-" + nodeName

                if (nodeName not in nodes.keys()):
                    continue

                podsSeenThisRound.add(podName)

                pod = nodes[nodeName].get(podName)
                if (not pod):
                    # we have to schedule the position after this loop
                    podsToBeInsertedThisRound[nodeName].append(Pod(podName, podStatus, nodeName, -1, podShortName))
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
                        print("Display too small, skipping node %s until we can allocate a position." % pod.name)
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
                for pod in pods:
                    if (not pod.name in podsSeenThisRound):
                        pod.status="Terminated"
                    r,g,b = PodStatusLed.status_color(pod.status)
                    # print("Setting %d %d %d %d" % (i, r, g, b))
                    blinkt.set_pixel(i, r, g, b)
                    i+=1
                offsetX += 1

            blinkt.show()
            time.sleep(1)

# Main function
if __name__ == "__main__":
    pod_status_led = PodStatusLed()
    pod_status_led.run()
