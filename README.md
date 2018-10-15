# Entangle-Python [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

wasd

## Install

Simply pip install from the github repo.

```bash
pip install entangle-python
```
## Usage

### Entanglement Server

Note that an entanglement object corresponds to a client.

```python
import entangle

# Define a callback for every new entanglement
def on_entangle(entanglement):
    def rprint(x):
        print(x)
        entanglement.test = x

    entanglement.rprint = rprint

# Listen for entanglements (listenes in blocking mode)
entangle.listen(host="localhost", port=12345, password="42", callback=on_entangle)
```

### Entanglement Client

If your script wants to connect to an entanglement server use the following.

```python
import entangle

def on_entangle(entanglement):
  entanglement.remote_fun("rprint")("Hello Universe!")
  entanglement.close()

# asyncronously connect to a client (entanglement spawns a daemon thread)
entangle.connect(host="localhost", port=12345, password="42", callback=on_entangle)
```
