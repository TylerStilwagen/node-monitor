from kubernetes import client, config
from pprint import pprint
from kubernetes.client.rest import ApiException
import time
from httplib2 import Http
from json import dumps
import os
from datetime import datetime, timedelta
import pytz

nodeToPodsDict = {}
clusterName = ""
queryTime = 60
hangoutThreadURL = ""

config.load_kube_config()


api_instance = client.CoreV1Api()

def readENVVariables():
    clusterName = os.environ['CLUSTER_NAME']
    queryTime = float(os.environ['QUERY_TIME'])
    hangoutThreadURL = os.environ['HANGOUT_URL']
    return clusterName,queryTime,hangoutThreadURL

def getWorkerNodesStatus():
    node_list = []
    try:
        print("Getting Nodes' Status") 
        # Get nodes from k8s api
        api_response = api_instance.list_node(include_uninitialized=True, pretty='true')
        node_list = api_response.items
        #Find nodes where Ready status is false
        unreadyNodes = getUnreadyNodes(node_list)
        #mapPodsToNode()
        #Send alerts for nodes not ready
        if len(unreadyNodes) != 0:
            print (unreadyNodes)
    except ApiException as e:
        print("Exception when calling CoreV1Api->list_node: %s\n" % e)

def getUnreadyNodes(node_list):
    unreadyNodes = []
    for node in node_list:
        nodeToPodsDict[node.metadata.name] = []
        node_ready = True
        node_status = node.status.conditions
        node_new = False
        time_created = node.metadata.creation_timestamp
        time_now = pytz.UTC.localize(datetime.utcnow())
        node_new = time_created - time_now < timedelta(minutes=90)
        for current_status in node_status:
            if current_status.type == 'Ready' and current_status.status == "False" and node_new == False:
                node_ready = False
                unreadyNodes.append(node)

        print(node.metadata.name + " ready: " + str(node_ready) + str(node_new))
    return unreadyNodes


print("Starting Kubernetes Monitor")
while True:
    getWorkerNodesStatus()
    time.sleep(queryTime)
