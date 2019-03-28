import entangle
import sys

if sys.argv[1] == "server":
    # Define a callback for every new entanglement
    def on_entangle(entanglement):
        def rprint(x):
            print(x)
            entanglement.test = x
            entanglement.remote_fun("done_rprint")()

        def shutdown():
            from twisted.internet import reactor
            print("Shutting down server.")
            reactor.stop()

        entanglement.rprint = rprint
        entanglement.shutdown = shutdown

    # Listen for entanglements (listenes in blocking mode)
    entangle.listen(host="localhost", port=24454, password="42", callback=on_entangle)
else:
    # connect to a client (network listener spawns a daemon thread)
    entanglement = entangle.connect(host="localhost", port=24454, password="42")

    # do something with the entanglement
    def done_rprint():
        print(entanglement.test)
        entanglement.remote_fun("shutdown")()
    entanglement.done_rprint = done_rprint
    entanglement.remote_fun("rprint")("Hello Universe!")
    
    # Wait until the connection is dropped
    entanglement.join()
