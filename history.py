#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
#
# The MIT License (MIT)
#
# Copyright (c) Crossbar.io Technologies GmbH
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
###############################################################################

from autobahn.twisted.websocket import WebSocketClientProtocol, WebSocketClientFactory
import json, os
import time
import thread
import gzip
import twisted

STORE_PATH = os.environ.get('STORE_PATH', '.')

dt_str = None;
KILL_TIME_DIFF = 60
kill_time = int(time.time()) + KILL_TIME_DIFF
RESTART_PERIOD = int(os.environ.get('RESTART_PERIOD', 60*60)) # 1 hour
kill_time2 = int(time.time()) + RESTART_PERIOD

my_timezone = 'Europe/Kiev'

def kill_by_timeout():
        global kill_time
        while kill_time > int(time.time()):
            time.sleep(1)
        if reactor.running:
            reactor.stop()

def kill_by_period():
        global kill_time2
        while kill_time2 > int(time.time()):
            time.sleep(1)
        print("Killing...")
        if reactor.running:
            reactor.stop()


class MyClientProtocol(WebSocketClientProtocol):
    def onConnect(self, response):
        global dt_str
        print("Server connected: {0}".format(response.peer))
        self.fo = open('%s/%s.txt'%(STORE_PATH, dt_str), 'a')
        self.fo_users = open('%s/%s_users.txt'%(STORE_PATH, dt_str), 'a')
        self.counter = 0
        self.counter2 = 0
        thread.start_new_thread(kill_by_timeout, ())

    def onOpen(self):
        print("WebSocket connection open.")
        #self.sendMessage(u"{type: \"placepixel\", x: 150, y: 30, color: 3}".encode('utf8'))

        '''
        def hello():
            self.sendMessage(u"Hello, world!".encode('utf8'))
            self.sendMessage(b"\x00\x01\x03\x04", isBinary=True)
            self.factory.reactor.callLater(1, hello)

        # start sending messages every second ..
        hello()
        '''

    def onMessage(self, payload, isBinary):
        global kill_time, KILL_TIME_DIFF
        kill_time = int(time.time()) + KILL_TIME_DIFF
        if isBinary:
            print("Binary message received: {0} bytes".format(len(payload)))
        else:
            #print("Text message received: {0}".format(payload.decode('utf8')))
            j = json.loads(payload.decode('utf8'))
            t = int(time.time())
            if j and j.get('type') == 'pixel':
                for p in j.get('pixels'):
                    s = "{0};{1};{2};{3}\n".format(t, p.get('x'), p.get('y'), p.get('color'))
                    self.fo.write(s)
                self.counter += 1
                if self.counter % 50 == 0:
                    self.fo.flush()
            elif j and j.get('type') == 'users':
                s = "{0};{1}\n".format(t, j.get('count'))
                self.fo_users.write(s)
                self.counter2 += 1
                if self.counter2 % 12 == 0:
                    self.fo_users.flush()
            else:
                print("Text message received: {0}".format(payload.decode('utf8')))

    def onClose(self, wasClean, code, reason):
        print("WebSocket connection closed: {0}".format(reason))
        if hasattr(self, 'fo'):
            self.fo.close()
        if hasattr(self, 'fo_users'):
            self.fo_users.close()
        try:
            reactor.stop()
        except:
            print "stop died!"

    def connectionLost(self,reason):
        #self.factory.connections.remove(self)
        WebSocketClientProtocol.connectionLost(self, reason)#always after your code
        if reactor.running:
            try:
                reactor.stop()
            except twisted.internet.error.ReactorNotRunning as e:
                pass

if __name__ == '__main__':

    import sys

    from twisted.python import log
    from twisted.internet import reactor
    from twisted.web.client import getPage
    from twisted.web.client import Agent, CookieAgent, readBody
    from cookielib import Cookie, CookieJar

    log.startLogging(sys.stdout)

    from datetime import datetime
    import pytz, time
    tm = datetime.fromtimestamp(time.time(), pytz.timezone(my_timezone))
    dt_str = '%d%02d%02d_%02d%02d%02d'%(tm.year, tm.month, tm.day, tm.hour, tm.minute, tm.second)
    #dt_str = '%d%02d%02d_%02d%02d%02d-%d'%(tm.year, tm.month, tm.day, tm.hour, tm.minute, tm.second, int(time.time()))

    url = 'http://pxls.space/boarddata'
    #pxls-agegate=1

    thread.start_new_thread(kill_by_period, ())

    # http://pxls.space/boarddata response
    def cbBody(data):
        with gzip.open("%s/%s.bin"%(STORE_PATH, dt_str), "wb") as file:
            file.write(data)
    def cbRequest(response):
        d = readBody(response)
        d.addCallback(cbBody)
        return d
 
    cj = CookieJar()
    c = Cookie(None, 'pxls-agegate', '1', '80', '80', 'pxls.space', 
       None, None, '/', None, False, False, 'TestCookie', None, None, None)
    cj.set_cookie(c)

    agent = CookieAgent(Agent(reactor), cj)
    #d = agent.request('GET', url)
    d = getPage(url, headers = {"Cookie": "pxls-agegate=1"})
    d.addCallback(cbBody)

    factory = WebSocketClientFactory(u"ws://pxls.space/ws", headers = {"Cookie": "pxls-agegate=1"})
    factory.protocol = MyClientProtocol

    reactor.connectTCP("pxls.space", 80, factory)
    reactor.run()
