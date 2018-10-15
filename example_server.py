import entangle
import sys
import time

# Define a callback for every new entanglement
def on_entangle(entanglement):
    while True:
        entanglement.test = "Hello from Python!"
        time.sleep(1)
        entanglement.test = "Hello Universe!"
        time.sleep(1)

# Listen for entanglements (listenes in blocking mode)
entangle.listen(host="localhost", port=12345, password="42", callback=on_entangle)
