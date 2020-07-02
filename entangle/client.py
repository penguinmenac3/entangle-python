#!/usr/bin/python

from autobahn.twisted.websocket import WebSocketClientProtocol, WebSocketClientFactory
from twisted.internet import reactor
from twisted.internet.ssl import ClientContextFactory
import json
import hashlib
import sys
import bcrypt
import warnings
import ssl
import time
import traceback
from threading import Thread, Condition

from entangle.entanglement import Entanglement


def create_client(host, port, password, callback, fail, user=None, non_main=False, use_ssl=False, run_reactor=True):
    class EntanglementClientProtocol(WebSocketClientProtocol):
        def close_entanglement(self):
            self.closedByMe = True
            self.sendClose()

        def onConnect(self, request):
            sys.stdout.flush()
            self.entanglement = Entanglement(self)
            salt = bcrypt.gensalt().decode("utf-8")
            saltedPW = password + salt
            computedHash = hashlib.sha256(saltedPW.encode("utf-8")).hexdigest()
            if user is None:
                self.sendMessage("{} {}".format(computedHash, salt).encode("utf-8"), False)
            else:
                self.sendMessage("{} {} {}".format(user, computedHash, salt).encode("utf-8"), False)
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
                    self.entanglement._notify(packet["variable"]["name"], packet["variable"]["value"])
                elif "call" in packet:
                    call_packet = packet["call"]
                    try:
                        fun = self.entanglement.__getattribute__(call_packet["name"])
                        args = call_packet["args"]
                        kwargs = call_packet["kwargs"]
                        fun(*args, **kwargs)
                    except:
                        error = traceback.format_exc()
                        errormsg = "Error when invoking {} on entanglement with args {} and kwargs {}.\n{}".format(call_packet["name"], call_packet["args"], call_packet["kwargs"], error)
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
            fail()
            on_close = getattr(self.entanglement, "on_close", None)
            if callable(on_close):
                on_close()
            sys.stdout.flush()
            reactor.stop()

    # Use the protocol to create a connection
    if not use_ssl:
        factory = WebSocketClientFactory(u"ws://" + host + ":" + str(port))
        factory.protocol = EntanglementClientProtocol
        reactor.connectTCP(host, port, factory)
    else:
        factory = WebSocketClientFactory(u"wss://" + host + ":" + str(port))
        factory.protocol = EntanglementClientProtocol
        reactor.connectSSL(host, port, factory, ClientContextFactory())
    if run_reactor:
        if non_main:
            reactor.run(installSignalHandlers=False)
        else:
            reactor.run()

class Client(object):
    def __init__(self, host, port, password, user=None, callback=None, blocking=False, use_ssl=False, run_reactor=True):
        self._entanglement = None
        self._failed = False
        self.thread = None
        self.condition = Condition()
        self.callback = callback
        if blocking:
            create_client(host, port, password, self.__on_entangle, self.__on_fail, user, use_ssl=use_ssl, run_reactor=run_reactor)
        else:
            self.thread = Thread(target=create_client, args=(host, port, password, self.__on_entangle, self.__on_fail, user, True, use_ssl, run_reactor))
            self.thread.setDaemon(True)
            self.thread.start()

    def __on_entangle(self, entanglement):
        self._entanglement = entanglement
        self._entanglement.join = self.join
        self._entanglement.is_alive = self.is_alive
        self.condition.acquire()
        self.condition.notify()
        self.condition.release()
        if self.callback is not None:
            self.callback(entanglement)

    def __on_fail(self):
        self._entanglement = None
        self._failed = True
        self.condition.acquire()
        self.condition.notify()
        self.condition.release()

    def get_entanglement(self):
        self.condition.acquire()
        while self._entanglement is None and not self._failed:
            self.condition.wait()
        self.condition.release()
        return self._entanglement

    def join(self):
        if self.thread is not None:
            self.thread.join()
            self.thread = None

    def is_alive(self):
        if self.thread is not None:
            return self.thread.is_alive()
        else:
            return False


def connect(host, port, password, callback=None, user=None, use_ssl=False):
    if callback is not None:
        warnings.simplefilter('always', DeprecationWarning)  # turn off filter
        warnings.warn("Do not use callback parameter with this method. Either use Client(...) or connect without callback param. The entanglement will be returned.",
                    category=DeprecationWarning,
                    stacklevel=2)
        warnings.simplefilter('default', DeprecationWarning)
    c = Client(host, port, password, callback=callback, user=user, use_ssl=use_ssl)
    return c.get_entanglement()


def connect_blocking(host, port, password, callback, use_ssl=False):
    warnings.simplefilter('always', DeprecationWarning)  # turn off filter
    warnings.warn("Call to deprecated function connect_blocking(...). Use Client(...) or connect(...) instead.",
                category=DeprecationWarning,
                stacklevel=2)
    warnings.simplefilter('default', DeprecationWarning)
    Client(host, port, password, callback=callback, blocking=True, use_ssl=use_ssl)
