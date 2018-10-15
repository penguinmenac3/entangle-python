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
    entangle.listen(host="localhost", port=12345, password="42", callback=on_entangle)
else:
    def on_entangle(entanglement):
        entanglement.remote_fun("rprint")("Hello Universe!")

        def done_rprint():
            print(entanglement.test)
            entanglement.remote_fun("shutdown")()

        entanglement.done_rprint = done_rprint

    # asyncronously connect to a client (entanglement spawns a daemon thread)
    entangle.connect_blocking(host="localhost", port=12345, password="42", callback=on_entangle)
