#!/usr/bin/python

from autobahn.twisted.websocket import WebSocketClientProtocol, WebSocketClientFactory
from twisted.internet import reactor
import json
import hashlib
import sys
import bcrypt
from threading import Thread

from entangle.entanglement import Entanglement


def __create_client(host, port, password, callback):
    class EntanglementClientProtocol(WebSocketClientProtocol):
        def close_entanglement(self):
            self.closedByMe = True
            self.sendClose()

        def onConnect(self, request):
            print("Entanglement created: {}".format(request.peer))
            sys.stdout.flush()
            self.entanglement = Entanglement(self)
            salt = bcrypt.gensalt()
            saltedPW = password + salt
            computedHash = hashlib.sha256(saltedPW.encode("utf-8")).hexdigest()
            self.sendMessage("{} {}".format(computedHash, salt).encode("utf-8"), False)
            if callback is not None:
                self.thread = Thread(target=callback, args=(self.entanglement,))
                self.thread.setDaemon(True)
                self.thread.start()

        def onOpen(self):
            pass

        def onMessage(self, payload, isBinary):
            if not isBinary:
                packet = json.loads(payload.decode("utf-8"))
                if "error" in packet:
                    print(packet["error"])
                    sys.stdout.flush()
                elif "variable" in packet:
                    self.entanglement.__dict__[packet["variable"]["name"]] = packet["variable"]["value"]
                elif "call" in packet:
                    call_packet = packet["call"]
                    try:
                        fun = self.entanglement.__getattribute__(call_packet["name"])
                        args = call_packet["args"]
                        kwargs = call_packet["kwargs"]
                        fun(*args, **kwargs)
                    except:
                        errormsg = "Error when invoking {} on entanglement with args {} and kwargs {}.".format(call_packet["name"], call_packet["args"], call_packet["kwargs"])
                        print(errormsg)
                        sys.stdout.flush()
                        result = {"error": errormsg}
                        self.sendMessage(json.dumps(result).encode("utf-8"), False)
                else:
                    self.close_entanglement()

        def call_method(self, function, args, kwargs):
            result = {"call": {"name": function, "args": args, "kwargs": kwargs}}
            self.sendMessage(json.dumps(result).encode("utf-8"), False)

        def update_variable(self, name, value):
            result = {"variable": {"name": name, "value": value}}
            self.sendMessage(json.dumps(result).encode("utf-8"), False)

        def onClose(self, wasClean, code, reason):
            print("Entanglement closed: {}".format(reason))
            sys.stdout.flush()
            reactor.stop()

    # Use the protocol to create a connection
    factory = WebSocketClientFactory(u"ws://" + host + ":" + str(port))
    factory.protocol = EntanglementClientProtocol

    reactor.connectTCP(host, port, factory)
    reactor.run()


def connect(host, port, password, callback):
    thread = Thread(target=__create_client, args=(host, port, password, callback))
    thread.setDaemon(True)
    thread.start()


def connect_blocking(host, port, password, callback):
    __create_client(host, port, password, callback)
