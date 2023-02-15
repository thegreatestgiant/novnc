#!/usr/bin/env python
import time
import subprocess
import argparse
import PySimpleGUI as sg
import re
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
        self.parser.add_argument("--max-x", help="max x pixels", default=64, type=int)
        self.parser.add_argument("--max-y", help="max y pixels", default=32, type=int)
        self.parser.add_argument("-n", "--namespace", help="Kubernetes namespace", default="github-actions-runner-link")
        self.parser.add_argument("--length", help="pixel length", default=8, type=int)
        self.parser.add_argument("--height", help="pixel height", default=8, type=int)
        self.parser.add_argument("--window-x",  help="window size x", default=800, type=int)
        self.parser.add_argument("--window-y",  help="window size y", default=600, type=int)
        self.parser.add_argument("nodes", action='store', nargs='+', default=["node64-1", "node64-2"])
        self.parser.add_argument("--dashboard-url", help="Kubernetes dashboard URL", default="http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/", type=str)

        self.args = self.parser.parse_args()

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
            'CreateContainerError': 'red',
            'ImagePullBackOff': 'red',
            'InvalidImageName': 'red',
            'Terminating': 'brown',
            'Completed': 'blue',
            'Pending': 'white',
            'ContainerCreating': 'yellow',
            'Terminated': 'grey',
            'Ready': 'black',
            'Ready,SchedulingDisabled': 'purple',
            'NotReady': 'grey'
        }.get(status, 'pink')

    def splitCamelCase(name):
        words= re.sub('([A-Z][a-z]+)', r' \1', re.sub('([A-Z]+)', r' \1', name)).split()
        for i in range (max(4-len(words),0)):
            words.append("")
        return "\n".join(words)

    def run(self):
        nodes = {}
        nodeStatus = {}
        nodesByPosition = {}
        positionsAlreadyTaken = {}
        objectAtPosition = {}
        fullScreen = True

        numberNodes=len(self.args.nodes)
        pixelsPerNodeRow = int(self.args.max_x/numberNodes)

        pixelsPerNodeColumn = self.args.max_y

        podPixelLength=self.args.length
        podPixelHeight=self.args.height

        namespace = self.args.namespace
        dashboardUrl = self.args.dashboard_url

        podsPerColumn = int(pixelsPerNodeColumn/podPixelHeight)

        podsPerNodeRow=int(pixelsPerNodeRow/podPixelLength)
        podsPerRow = podsPerNodeRow * numberNodes

        positionMax = podsPerNodeRow * podsPerColumn

        layout1 = []
        layout2 = []
        offsetX = 0
        for node in self.args.nodes:
            nodes[node] = {}
            nodeStatus[node] = "NotReady"
            nodesByPosition[node] = []
            positionsAlreadyTaken[node] = set()

            frameLayout1 = []
            frameLayout2 = []
            for j in range (podsPerColumn):
                row1 = []
                row2 = []
                for i in range(podsPerNodeRow):
                    row1.append(sg.Button(PodStatusLed.splitCamelCase("Unknown"), button_color=('black', 'grey'),
                                key=(0, i + offsetX, j), tooltip="Nothing to see here", disabled=True, border_width=3, pad=(5,5), size=(podPixelLength, podPixelHeight)))

                    row2.append(sg.Button(PodStatusLed.splitCamelCase("Unknown"), button_color=('black', 'grey'),
                                key=(1, i + offsetX, j), tooltip="Nothing to see here", disabled=True, border_width=3, pad=(5,5), size=(podPixelLength, podPixelHeight)))

                frameLayout1.append(row1)
                frameLayout2.append(row2)

            offsetX += podsPerNodeRow
            layout1.append(sg.Frame(layout=frameLayout1, title="%s: Unknown" % node, key=(0, node)))
            layout2.append(sg.Frame(layout=frameLayout2, title="%s: Unknown" % node, key=(1, node)))

        layout = [[sg.Column(layout=[layout1], key=0),
            sg.Column(layout=[layout2], visible=False, key=1)]]

        #window = sg.Window('Pod Status', font='Any 9', border_depth=2, no_titlebar=True, size=(800,600)).Layout(layout).Finalize()
        # window = sg.Window('Pod Status', font='Any 7', border_depth=2, size=(self.args.window_x,self.args.window_y)).Layout(layout).Finalize()
        window = sg.Window('Pod Status', font='Any 7', margins=(0,0), border_depth=3).Layout(layout).Finalize()
        window.Maximize()

        activeLayout=0
        while True:

            event, values = window.read(timeout=3000, timeout_key="timeout")
            if event == sg.WIN_CLOSED:
                break

            if event != "timeout":
                object = objectAtPosition[event[0], event[1], event[2]]

                # We may introduce more pod related ops later
                if object not in self.args.nodes:
                    # print (subprocess.getoutput(("kubectl delete pod '%s' --namespace '%s'") % (object, namespace)))
                    # subprocess.Popen(["kubectl", "delete", "pods", object, "--namespace", namespace])
                    url = "%s/#/pod/%s/%s/?namespace=%s" % (dashboardUrl, namespace, object, namespace)
                    print (url)
                    subprocess.Popen(["open", url ])
                else:
                    # node related or general op

                    layoutD = [
                        [sg.Text('Operations')],
                        [sg.Radio('Toggle full screen', "operations", default=True), sg.Radio('Drain node', "operations"), sg.Radio('Cordon node', "operations"), sg.Radio('Uncordon node', "operations")],
                        [sg.Submit(), sg.Cancel()]
                    ]

                    windowD = sg.Window('Possible operations', layoutD)

                    event, values = windowD.read()
                    windowD.close()

                    if (event == "Submit"):
                        if values[0]:
                            # toggle full screen
                            if fullScreen:
                                window.Normal()
                                fullScreen = False
                            else:
                                window.Maximize()
                                fullScreen = True
                        elif values[1]:
                            # drain node
                            subprocess.Popen(["kubectl", "drain", object, "--ignore-daemonsets", "--delete-local-data"])
                        elif values[2]:
                            # cordon node
                            subprocess.Popen(["kubectl", "cordon", object])
                        elif values[3]:
                            # uncordon node
                            subprocess.Popen(["kubectl", "uncordon", object])


            # reset offscreen layout after each cycle
            offsetX = 0
            for node in self.args.nodes:
                for j in range (podsPerColumn):
                    for i in range(podsPerNodeRow):
                        window[((activeLayout+1)%2, i + offsetX, j)].update(PodStatusLed.splitCamelCase(" "), button_color=('black', 'grey'), disabled=False)
                        window[((activeLayout+1)%2, i + offsetX, j)].SetTooltip("Click for possible node operations")
                        objectAtPosition[((activeLayout+1)%2, i + offsetX, j)]=node
                offsetX += podsPerNodeRow

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
                    print ("Node %s not displayed on display, ignoring pod %s" % (nodeName, podName))
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
                textColor=PodStatusLed.status_color(nodeStatus[node])
                window[((activeLayout+1)%2, node)].update("%s: %s" % (node, nodeStatus[node]))

                for pod in pods:
                    if (not pod.name in podsSeenThisRound):
                        pod.status="Terminated"
                    basePosX = i  % podsPerNodeRow
                    basePosY = (int) (i/podsPerNodeRow)
                    color = PodStatusLed.status_color(pod.status)
                    window[((activeLayout+1)%2, basePosX + offsetX, basePosY)].update(PodStatusLed.splitCamelCase(pod.status), button_color=(textColor, color), disabled=False)
                    if (pod.status != 'Terminated'):
                        window[((activeLayout+1)%2, basePosX + offsetX, basePosY)].SetTooltip("Click to get dashboard for pod %s" % pod.shortName)
                        objectAtPosition[((activeLayout+1)%2, basePosX + offsetX, basePosY)]=pod.shortName
                    i+=1
                offsetX += podsPerNodeRow

            window[activeLayout].update(visible=False)
            activeLayout=(activeLayout+1)%2
            window[activeLayout].update(visible=True)
            window.refresh()

# Main function
if __name__ == "__main__":
    pod_status_led = PodStatusLed()
    pod_status_led.run()
