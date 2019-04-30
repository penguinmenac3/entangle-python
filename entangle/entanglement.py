from threading import Condition

class Entanglement(object):
    """
    An entanglement entangles two objects on different machines via the network.

    Variables are synced. Functions are passed for remote invokation.
    Functions will not pass their return type! (Assumed void functions)

    If you get a non-existent variable you get a remote function caller.
    If you set variables they are pushed to the remote.
    If you set a function it is a handler for remote function calls.
    """
    def __init__(self, protocol):
        self.__protocol = protocol
        self.__condition = Condition()

    def __setattr__(self, name, value):
        super(Entanglement, self).__setattr__(name, value)
        if not name.startswith("_"):
            self._notify(name, value, write=False)
        if not callable(value) and not name.startswith("_"):
            self.__protocol.update_variable(name, value)

    def remote_fun(self, name):
        def fun(*args, **kwargs):
            self.__protocol.call_method(name, args, kwargs)
        return fun

    def close(self):
        self.__protocol.close_entanglement()

    def get(self, variablename):
        """
        Waits with returning until the value is not none.
        """
        self.__condition.acquire()
        while variablename not in self.__dict__ or self.__dict__[variablename] is None:
            self.__condition.wait()
        self.__condition.release()

        return self.__dict__[variablename]

    def _notify(self, variablename, value, write=True):
        if write:
            self.__dict__[variablename] = value
        self.__condition.acquire()
        self.__condition.notify()
        self.__condition.release()
