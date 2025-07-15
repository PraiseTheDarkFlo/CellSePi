from typing import Tuple
from src.cellsepi.backend.main_window.expert_mode.event_manager import *
from src.cellsepi.backend.main_window.expert_mode.listener import *
import pytest

class DummyEvent(Event):
    def __init__(self):
        self.test = "test"

class DummyListener(EventListener):
    def __init__(self):
        self.last_event: ProgressEvent | None = None
        self.event_type = ProgressEvent

    def get_event_type(self) -> Type[Event]:
        return self.event_type

    def _update(self,event: Event) -> None:
        self.last_event = event


def test_notify_listener():
    manager = EventManager()
    listener = DummyListener()

    manager.subscribe(listener=listener)
    event = ProgressEvent(0,"test")
    assert manager._listeners[type(event)] == [listener]

    manager.notify(event)
    assert listener.last_event.percent == 0, "Something went wrong when notifying the listener"
    assert listener.last_event.name == "test", "Something went wrong when notifying the listener"

    manager.unsubscribe(listener=listener)
    assert len(manager._listeners) == 0, "Something went wrong when unsubscribed"

    listener.last_event = None
    manager.notify(event)
    assert listener.last_event is None, "Listener was notified after unsubscribe"


def test_event_listener_update_wrong_type():
    listener = DummyListener()
    with pytest.raises(TypeError):
        listener.update(DummyEvent())

def test_unsubscribe_never_subscribed():
    manager = EventManager()
    listener = DummyListener()
    with pytest.raises(ValueError):
        manager.unsubscribe(listener=listener)