class Notifier:
    def __init__(self):
        self._start_listeners = set()
        self._update_listeners = set()
        self._completion_listeners = set()

    def _call_listeners(self, listeners, args, kwargs):
        for listener in listeners:
            listener(*args, **kwargs)

    def add_start_listener(self, listener):
        self._start_listeners.add(listener)

    def remove_start_listener(self, listener):
        self._start_listeners.remove(listener)

    def _call_start_listeners(self, *args, **kwargs):
        self._call_listeners(self._start_listeners, args, kwargs)

    def add_update_listener(self, listener):
        self._update_listeners.add(listener)

    def remove_update_listener(self, listener):
        self._update_listeners.remove(listener)

    def _call_update_listeners(self, *args, **kwargs):
        self._call_listeners(self._update_listeners, args, kwargs)

    def add_completion_listener(self, listener):
        self._completion_listeners.add(listener)

    def remove_completion_listener(self, listener):
        self._completion_listeners.remove(listener)

    def _call_completion_listeners(self, *args, **kwargs):
        self._call_listeners(self._completion_listeners, args, kwargs)

    def add_cancel_listener(self, listener):
        self._completion_listeners.add(listener)

    def remove_cancel_listener(self, listener):
        self._completion_listeners.remove(listener)

    def _call_cancel_listeners(self, *args, **kwargs):
        self._call_listeners(self._completion_listeners, args, kwargs)
