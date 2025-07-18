from abc import ABC, abstractmethod
from typing import List, Type, TypeVar, Generic
from cellsepi.backend.main_window.expert_mode.listener import *

class EventManager:
    """
    Manages the different Listeners and notify them if they associated event happens.
    """
    def __init__(self):
        self._listeners: dict[Type[Event], List[EventListener]] = {}

    def subscribe(self, listener: EventListener):
        event_type = listener.get_event_type()
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(listener)

    def unsubscribe(self, listener: EventListener):
        event_type = listener.get_event_type()
        if event_type not in self._listeners or listener not in self._listeners[event_type]:
            raise ValueError("Listener is not subscribed")
        self._listeners[event_type].remove(listener)
        if len(self._listeners[event_type]) == 0:
            del self._listeners[event_type]

    def notify(self,event: Event):
        event_type = type(event)
        print(event_type)
        if event_type not in self._listeners:
            print("Listener is not subscribed")
            return
        for listener in self._listeners.get(event_type, []):
            print("Notifying listener", listener)
            listener.update(event)