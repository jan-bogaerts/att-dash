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

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, rc):
    global _mqttConnected
    if rc == 0:
        _mqttConnected = True
        logging.info("Connected to mqtt broker with result code "+str(rc))
        if _callbacks:
            for asset, callback in _callbacks.iteritems():
                _subscribe(asset)
                curVal = getAssetState(asset)
                if curVal:
                    if 'state' in curVal:
                        callback(curVal['state'])
                    elif 'value' in curVal:
                        callback(curVal)
    else:
        print("Failed to connect to mqtt broker: "  + mqtt.connack_string(rc))


# The callback for when a PUBLISH message is received from the server.
def on_MQTTmessage(client, userdata, msg):
    global _lastMessage
    payload = str(msg.payload)
    topicParts = msg.topic.split("/")
    if topicParts[4] in _callbacks:
        value = json.loads(msg.payload)
        callback = _callbacks[topicParts[4]]
        callback(value)										#we want the second last value in the array, the last one is 'command'

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
    global  _access_token, _refresh_token, _expires_in, _mqttClient, _httpClient, _mqttConnected, _callbacks, _brokerPwd, _brokerUser
    if not resumable:
        _access_token = None
        _refresh_token = None
        _expires_in = None
        for asset, callback in _callbacks.iteritems():
            _unsubscribe(asset)
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
    """monitor for changes for that asset
    :type callback: function, format: callback(json_object)
    :param callback: a function that will be called when a value arrives for the specified asset.
    :type asset: string
    :param asset: the id of the assset to monitor
    """
    _callbacks[asset] = callback
    if _mqttClient and _mqttConnected == True:
        _subscribe(asset)

def unsubscribe(asset):
    if asset in _callbacks:
        _callbacks.pop(asset)
        if _mqttClient and _mqttConnected == True:
            _unsubscribe(asset)

def _subscribe(asset):
    topic = str("client/" + _clientId + "/in/asset/" + asset + "/state")        # asset is usually a unicode string, mqtt trips over this.
    logging.info("subscribing to: " + topic)
    result = _mqttClient.subscribe(topic)                                                    #Subscribing in on_connect() means that if we lose the connection and reconnect then subscriptions will be renewed.
    logging.info(str(result))

def _unsubscribe(asset):
    topic = str("client/" + _clientId + "/in/asset/" + asset + "/state")        # asset is usually a unicode string, mqtt trips over this.
    logging.info("subscribing to: " + topic)
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

def getGrounds(includeShared):
    """get all the grounds related to the current account.
    :type includeShared: bool
    :param includeShared: when true, shared grounds will also be included
    """
    url = "/me/grounds"
    if includeShared:
        params = urllib.urlencode({'type': "shared"})
    else:
        params = None
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

def send(id, value):
    typeOfVal = type(value)
    body = {"value": value }
    body = json.dumps(body)

    url = "/asset/" +  id + "/command"

    result = doHTTPRequest(url, body, "PUT")