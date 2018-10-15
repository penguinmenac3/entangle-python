#!/usr/bin/python

from autobahn.twisted.websocket import WebSocketServerProtocol, WebSocketServerFactory
from twisted.internet import reactor
import json
import hashlib
import sys
from threading import Thread

from entangle.entanglement import Entanglement


def listen(host, port, password, callback):
    """
    Listen for entanglements.

    You should set EntanglementProtocol.callback to receive the entanglements.
    Further it is recommended to set EntanglementProtocol.password to have a password protection.
    """
    class EntanglementServerProtocol(WebSocketServerProtocol):
        def close_entanglement(self):
            self.closedByMe = True
            self.sendClose()

        def onConnect(self, request):
            print("Entanglement created: {}".format(request.peer))
            sys.stdout.flush()
            self.entanglement = Entanglement(self)
            self.authenticated = False

        def onOpen(self):
            pass

        def onMessage(self, payload, isBinary):
            if not isBinary:
                if not self.authenticated:
                    auth = payload.decode("utf-8").split(" ")
                    receivedHash = auth[0]
                    receivedSalt = auth[1]
                    saltedPW = password + receivedSalt
                    computedHash = hashlib.sha256(saltedPW.encode("utf-8")).hexdigest()
                    if computedHash == receivedHash:
                        self.authenticated = True
                        if callback is not None:
                            self.thread = Thread(target=callback, args=(self.entanglement,))
                            self.thread.setDaemon(True)
                            self.thread.start()
                    else:
                        self.close_entanglement()
                else:
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

    factory = WebSocketServerFactory(u"ws://" + host + ":" + str(port))
    factory.protocol = EntanglementServerProtocol
    # factory.setProtocolOptions(maxConnections=2)

    reactor.listenTCP(port, factory)
    reactor.run()


if __name__ == "__main__":
    import sys
    listen(sys.argv[1], sys.argv[2])
