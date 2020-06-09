# Entangle-Python [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Did you ever think syncing variables between two processes (anywhere in the world) is difficult?
Entangle-Python is your solution.
It enables you to entangle two variables across processes.
One needs to launch an entanglement server and one an entanglement client.
You can connect entanglements even cross programming language.

You can see the documentation below or simply look at some examples.

A python server and client in one script can be found [here](https://github.com/penguinmenac3/entangle-python/blob/master/example.py).
If you want only a server to which for example [entangle-js](https://github.com/penguinmenac3/entangle-js) can connect to, check out [this script](https://github.com/penguinmenac3/entangle-python/blob/master/example_server.py).

## Install

Simply pip install the package.

```bash
pip install entangle-python
```

### Creating an SSL Certificate

SSL Certificates are required for SSL encryption (this is optional but highly recommended).

Create a folder where your certs should live and create a password with or without a password.

```bash
mkdir certs
cd certs

# with password (secure)
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365
# or without passwort (insecure)
#openssl req -x509 -nodes -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365
```

## Usage

### Entanglement Server

Listen for entanglement requests and handle them.
Inside the callback you can do whatever you want, it is a new thread and does not hinder new entanglements from happening.
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
entangle.listen(host="localhost", port=12345, password="42", callback=on_entangle, ssl_root="certs")
```

### Entanglement Client

If your script wants to connect to an entanglement server use the following.
The connect function connects asynchronously to a server.
Once an entanglement is established your callback gets called.

```python
import entangle

def on_entangle(entanglement):
  entanglement.remote_fun("rprint")("Hello Universe!")
  entanglement.close()

# asynchronously connect to a client (entanglement spawns a daemon thread)
entangle.connect(host="localhost", port=12345, password="42", callback=on_entangle, use_ssl=True)
```
