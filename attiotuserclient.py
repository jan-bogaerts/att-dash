__author__ = 'Jan Bogaerts'
__copyright__ = "Copyright 2015, AllThingsTalk"
__credits__ = []
__maintainer__ = "Jan Bogaerts"
__email__ = "jb@allthingstalk.com"
__status__ = "Prototype"  # "Development", or "Production"

import paho.mqtt.client as mqtt
import logging
import json
import httplib                                 # for http comm
import urllib                                   # for http params
import time
from socket import error as SocketError         # for http error handling
import errno

_mqttClient = None
_mqttConnected = False
_httpClient = None
_callbacks = {}
_get_assets_callback = None

_curHttpServer = None
_access_token = None
_refresh_token = None
_expires_in = None
_clientId = None
_brokerUser = None
_brokerPwd = None
_isLoggedIn = False                                     # keeps track if user is logged in or not, so we can show the correct errors.

class SubscriberData:
    """
    callback: function to call when data arrived.
    direction: 'in' (from cloud to client) or 'out' (from device to cloud)
    toMonitor: 'state': changes in the value of the asset, 'command' actuator commands, 'events': device/asset/... creaated, deleted,..
    level: 'asset', 'device', 'gateway', 'ground' # 'all device-assets', 'all gateway-assets', 'all gateway-devices', 'all gateway-device-assets'
    """
    def __init__(self):
        self.id = None
        self.callback = None
        self.direction = 'in'
        self.toMonitor = 'state'
        self.level = 'asset'

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, rc):
    global _mqttConnected
    try:
        if rc == 0:
            _mqttConnected = True
            logging.info("Connected to mqtt broker with result code "+str(rc))
            if _callbacks:
                for topic, definitions in _callbacks.iteritems():
                    _subscribe(topic)
                    for definition in definitions:
                        if definition.level == 'asset' and definition.direction == 'in' and definition.toMonitor == 'state':    # refresh the state of all assets being monitored when reconnecting. Other events can't be refreshed.
                            curVal = getAssetState(definition.id)
                            if curVal:
                                if 'state' in curVal:
                                    definition.callback(curVal['state'])
                                elif 'value' in curVal:
                                    definition.callback(curVal)
        else:
            logging.error("Failed to connect to mqtt broker: " + mqtt.connack_string(rc))
    except Exception:
        logging.exception("failed to connect")


# The callback for when a PUBLISH message is received from the server.
def on_MQTTmessage(client, userdata, msg):
    global _lastMessage
    try:
        if msg.topic in _callbacks:
            topicParts = msg.topic.split('/')
            logging.info(str(topicParts))
            if topicParts[2] == 'in':                   # data from cloud to client is always json, from device to cloud is not garanteed to be json.
                value = json.loads(msg.payload)
            else:
                value = msg.payload
            defs = _callbacks[msg.topic]
            for definition in defs:
                definition.callback(value)
    except Exception as e:
        if msg.payload:
            logging.exception("failed to process incomming message" + str(msg.payload))
        else:
            logging.exception("failed to process incomming message")

def on_MQTTSubscribed(client, userdata, mid, granted_qos):
    logging.info("Subscribed to topic, receiving data from the cloud: qos=" + str(granted_qos))

def connect(username, pwd, httpServer, mqttServer):
    '''start the mqtt client and make certain that it can receive data from the IOT platform
	   mqttServer: (optional): the address of the mqtt server. Only supply this value if you want to a none standard server.
	   port: (optional) the port number to communicate on with the mqtt server.
    '''
    global _brokerPwd, _brokerUser
    mqttCredentials = connectHttp(username, pwd, httpServer)
    if not "rmq:clientId" in mqttCredentials:
        logging.error("username not specified, can't connect to broker")
        raise Exception("username not specified, can't connect to broker")
    _brokerUser = mqttCredentials["rmq:clientId"] + ":" + mqttCredentials["rmq:clientId"]
    _brokerPwd = mqttCredentials["rmq:clientKey"]

    _subscribe_mqtt(mqttServer)

def reconnect(httpServer, mqttServer):
    global _httpClient, _curHttpServer
    _httpClient = httplib.HTTPConnection(httpServer)
    _curHttpServer = httpServer             #so we can reconnect if needed
    _subscribe_mqtt(mqttServer)             #subscrriptions will be made after the connection is established

def disconnect(resumable = False):
    """close all connections to the cloud and reset the module
    if resumable is True, then only the network connections get closed, but the connection data remains, so that
    you can restart connections using the reconnect features.
    """
    global  _access_token, _refresh_token, _expires_in, _mqttClient, _httpClient, _mqttConnected, _callbacks, _brokerPwd, _brokerUser, _isLoggedIn
    if not resumable:
        _isLoggedIn = False
        _access_token = None
        _refresh_token = None
        _expires_in = None
        for topic, callback in _callbacks.iteritems():
            _unsubscribe(topic)
        _callbacks = {}
        _brokerPwd = None
        _brokerUser = None
    if _mqttClient:
        _mqttClient.disconnect()
        _mqttClient = None
    _mqttConnected = False
    if _httpClient:
        _httpClient.close()
    _httpClient = None

def subscribe(asset, callback):
    """monitor for changes for that asset. For more monitor features, use 'subscribeAdv'
    :type callback: function, format: callback(json_object)
    :param callback: a function that will be called when a value arrives for the specified asset.
    :type asset: string
    :param asset: the id of the assset to monitor
    """
    data = SubscriberData()
    data.id = asset
    data.callback = callback
    topic = _getTopic(data)
    if topic in _callbacks:
        _callbacks[topic].append(data)
    else:
        _callbacks[topic] = [data]
    if _mqttClient and _mqttConnected == True:
        _subscribe(topic)

def subscribeAdv(subscriberData):
    """subscribe to topics with advanced parameter options"""
    topic = _getTopic(subscriberData)
    if topic in _callbacks:
        _callbacks[topic].append(subscriberData)
    else:
        _callbacks[topic] = [subscriberData]
    if _mqttClient and _mqttConnected == True:
        _subscribe(topic)

def unsubscribe(id, level = 'asset'):
    """
    remove all the callbacks for the specified id.
    :param level: which type of item: asset, device, gateway
    :param id: the id of the item (asset, device, gateway,..) to remove
    """
    desc = SubscriberData()
    desc.id = id
    desc.level = level
    for direction in ['in', 'out']:
        desc.direction = direction
        for toMonitor in ['state', 'event', 'command']:
            desc.toMonitor = toMonitor
            topic = _getTopic(desc)
            if topic in _callbacks:
                _callbacks.pop(topic)
                if _mqttClient and _mqttConnected == True:
                    _unsubscribe(topic)


def getOutPath(assetId):
    """converts the asset id to a path of gateway id /device name / asset name or device id / asset name"""
    result = {}
    asset = getAsset(assetId)
    result['asset'] = asset['name']
    device = getDevice(asset['deviceId'])
    if device:
        if 'gatewayId' in device and device['gatewayId']:
            result['device'] = device['name']
            result['gateway'] = device['gatewayId']
        else:
            result['device'] = device['id']
    else:
        gateway = getGateway(asset['deviceId'])
        if gateway:
            result['gateway'] = gateway['id']
        else:
            raise Exception("asset does not belong to a device or gateway")
    return result

def _getTopic(desc):
    """
    generate topic
    :param desc: description of the topic to make
    """
    if desc.level == 'asset':
        if isinstance(desc.id, dict):
            if 'gateway' in desc.id:
                if 'device' in desc.id:
                    return str("client/" + _clientId + "/" + desc.direction + "/gateway/" + desc.id['gateway'] + "/device/" + desc.id['device'] + "/asset/" + desc.id['asset'] + "/" + desc.toMonitor)
                else:
                    return str("client/" + _clientId + "/" + desc.direction + "/gateway/" + desc.id['gateway'] + "/asset/" + desc.id['asset'] + "/" + desc.toMonitor)
            else:
                return str("client/" + _clientId + "/" + desc.direction + "/device/" + desc.id['device'] + "/asset/" + desc.id['asset'] + "/" + desc.toMonitor)
        else:
            return str("client/" + _clientId + "/" + desc.direction + "/asset/" + desc.id + "/" + desc.toMonitor)        # asset is usually a unicode string, mqtt trips over this.
    #todo: add topic renderers for different type of topics.
    raise NotImplementedError()

def _subscribe(topic):
    """
        internal subscribe routine
    :param desc: description of the subscription to make
    """
    logging.info("subscribing to: " + topic)
    result = _mqttClient.subscribe(topic)                                                    #Subscribing in on_connect() means that if we lose the connection and reconnect then subscriptions will be renewed.
    logging.info(str(result))

def _unsubscribe(topic):
    logging.info("unsubscribing to: " + topic)
    result = _mqttClient.unsubscribe(topic)                                                    #Subscribing in on_connect() means that if we lose the connection and reconnect then subscriptions will be renewed.
    logging.info(str(result))

def _subscribe_mqtt(broker):
    global _mqttClient                                             # we assign to these vars first, so we need to make certain that they are declared as global, otherwise we create new local vars
    if _brokerPwd and _brokerUser:
        if _mqttClient:
            _mqttClient.disconnect()
        _mqttClient = mqtt.Client()
        _mqttClient.on_connect = on_connect
        _mqttClient.on_message = on_MQTTmessage
        _mqttClient.on_subscribe = on_MQTTSubscribed
        _mqttClient.username_pw_set(_brokerUser, _brokerPwd)

        _mqttClient.connect(broker, 1883, 60)
        _mqttClient.loop_start()
    else:
        raise Exception("no mqtt credentials found")

def extractHttpCredentials(data):
    global _access_token, _refresh_token, _expires_in, _clientId
    if data:
        _access_token = data['access_token']
        _refresh_token = data['refresh_token']
        _expires_in = time.time() + data['expires_in']
        _clientId = data['rmq:clientId']
    else:
        _access_token = None
        _refresh_token = None
        _expires_in = None
        _clientId = None

def connectHttp(username, pwd, httpServer):
    global _httpClient, _curHttpServer
    _curHttpServer = httpServer
    _httpClient = httplib.HTTPConnection(httpServer)
    loginRes = login(username, pwd)
    extractHttpCredentials(loginRes)
    return loginRes

def login(username, pwd):
    global _isLoggedIn
    url = "/login"
    body = "grant_type=password&username=" + username + "&password=" + pwd + "&client_id=maker"
    print("HTTP POST: " + url)
    print("HTTP BODY: " + body)
    _httpClient.request("POST", url, body, {"Content-type": "application/json"})
    response = _httpClient.getresponse()
    logging.info(str((response.status, response.reason)))
    jsonStr =  response.read()
    logging.info(jsonStr)
    if response.status == 200:
        _isLoggedIn = True
        return json.loads(jsonStr)
    else:
        _processError(jsonStr)

def _processError(str):
    obj = json.loads(str)
    if obj:
        if 'error_description' in obj:
            raise Exception(obj['error_description'])
        elif 'message' in obj:
            raise Exception(obj['message'])
    raise Exception(str)

def refreshToken():
    """no need for error handling, is called within doHTTPRequest, which does the error handling"""
    global _access_token, _refresh_token
    url = "/login"
    body = "grant_type=refresh_token&refresh_token=" + _refresh_token + "&client_id=dashboard"
    print("HTTP POST: " + url)
    print("HTTP BODY: " + body)
    _httpClient.request("POST", url, body, {"Content-type": "application/json"})
    response = _httpClient.getresponse()
    logging.info(str((response.status, response.reason)))
    jsonStr =  response.read()
    logging.info(jsonStr)
    if response.status == 200:
        loginRes = json.loads(jsonStr)
    else:
        loginRes = None
    extractHttpCredentials(loginRes)

def getAsset(id):
    """get the details for the specified asset"""
    url = "/asset/" + id
    return doHTTPRequest(url, "")

def getAssetState(id):
    """get the details for the specified asset"""
    url = "/asset/" + id + '/state'
    return doHTTPRequest(url, "")

def getGateway(id):
    """get the details for the specified gateway"""
    url = "/gateway/" + id
    return doHTTPRequest(url, "")

def getGrounds(includeShared):
    """get all the grounds related to the current account.
    :type includeShared: bool
    :param includeShared: when true, shared grounds will also be included
    """
    url = "/me/grounds"
    if includeShared:
        url += '?' + urllib.urlencode({'type': "shared"})
    result = doHTTPRequest(url, "")
    if result:
        return result['items']

def getDevices(ground):
    """get all the devices related to a ground"""
    url = "/ground/" + ground + "/devices"
    result = doHTTPRequest(url, "")
    if result:
        return result['items']

def getDevice(deviceId):
    """get all the devices related to a ground"""
    url = "/device/" + deviceId
    return doHTTPRequest(url, "")

def getAssets(device):
    """"get all the assets for a device"""
    url = "/device/" + device
    result = doHTTPRequest(url, "")
    if result:
        return result['assets']

def _reconnectAfterSendData():
    try:
        global _httpClient
        _httpClient.close()
        _httpClient = httplib.HTTPConnection(_curHttpServer)  # recreate the connection when something went wrong. if we don't do this and an error occured, consecutive requests will also fail.
    except:
        logging.exception("reconnect failed after _sendData produced an error")

def doHTTPRequest(url, content, method = "GET"):
    """send the data and check the result
        Some multi threading applications can have issues with the server closing the connection, if this happens
        we try again
    """
    if _isLoggedIn:
        success = False
        badStatusLineCount = 0                              # keep track of the amount of 'badStatusLine' exceptions we received. If too many raise to caller, otherwise retry.
        while not success:
            try:
                if _expires_in < time.time():               #need to refesh the token first
                    refreshToken()
                headers = {"Content-type": "application/json", "Authorization": "Bearer " + _access_token}
                print("HTTP " + method + ': ' + url)
                print("HTTP HEADER: " + str(headers))
                print("HTTP BODY: " + content)
                _httpClient.request(method, url, content, headers)
                response = _httpClient.getresponse()
                logging.info(str((response.status, response.reason)))
                jsonStr =  response.read()
                logging.info(jsonStr)
                if response.status == 200:
                    if jsonStr: return json.loads(jsonStr)
                    else: return                                                    # get out of the ethernal loop
                elif not response.status == 200:
                    _processError(jsonStr)
            except httplib.BadStatusLine:                   # a bad status line is probably due to the connection being closed. If it persists, raise the exception.
                badStatusLineCount =+ 1
                if badStatusLineCount < 10:
                    _reconnectAfterSendData()
                else:
                    raise
            except (SocketError) as e:
                _reconnectAfterSendData()
                if e.errno != errno.ECONNRESET:             # if it's error 104 (connection reset), then we try to resend it, cause we just reconnected
                    raise
            except:
                _reconnectAfterSendData()
                raise
    else:
        raise Exception("Not logged in: please check your credentials")

def send(id, value):
    typeOfVal = type(value)
    body = {"value": value }
    body = json.dumps(body)

    url = "/asset/" +  id + "/command"

    result = doHTTPRequest(url, body, "PUT")