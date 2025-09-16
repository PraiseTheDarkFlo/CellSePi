import flet as ft

from cellsepi.backend.main_window.expert_mode.module import Module, Port, ModuleGuiConfig
from cellsepi.backend.main_window.expert_mode.pipeline import Pipeline, PipelineRunningException
from cellsepi.backend.main_window.expert_mode.event_manager import *
from cellsepi.backend.main_window.expert_mode.listener import *
import pytest

class DummyErrorModule(Module):
    def __init__(self, module_id: str):
        self._name = module_id
        self._event_manager = None

    @classmethod
    def gui_config(cls) -> ModuleGuiConfig:
        return ModuleGuiConfig("ErrorModule", None, None)

    @property
    def module_id(self) -> str:
        return self._name

    @property
    def inputs(self) -> dict[str, Port]:
        return {}

    @property
    def outputs(self) -> dict[str, Port]:
        return {}

    @property
    def settings(self) -> ft.Container:
        pass

    @property
    def event_manager(self) -> EventManager:
        return self._event_manager

    @event_manager.setter
    def event_manager(self, value: EventManager):
        self._event_manager = value


    def run(self):
        raise PipelineRunningException("test","test")

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

class DummyErrorListener(EventListener):
    def __init__(self):
        self.last_event: ErrorEvent | None = None
        self.event_type = ErrorEvent

    def get_event_type(self) -> Type[Event]:
        return self.event_type

    def _update(self,event: Event) -> None:
        print("ERROR")
        self.last_event = event

class DummyModuleListener(EventListener):
    def __init__(self):
        self.last_event: ModuleExecutedEvent | None = None
        self.event_type = ModuleExecutedEvent

    def get_event_type(self) -> Type[Event]:
        return self.event_type

    def _update(self, event: Event) -> None:
        self.last_event = event


def test_notify_listener():
    manager = EventManager()
    listener = DummyListener()

    manager.subscribe(listener=listener)
    event = ProgressEvent(0,"test")
    assert manager._listeners[type(event)] == [listener]

    manager.notify(event)
    assert listener.last_event.percent == 0, "Something went wrong when notifying the listener"
    assert listener.last_event.process == "test", "Something went wrong when notifying the listener"

    manager.unsubscribe(listener=listener)
    assert len(manager._listeners) == 0, "Something went wrong when unsubscribed"

    listener.last_event = None
    manager.notify(event)
    assert listener.last_event is None, "Listener was notified after unsubscribe"

def test_module_listener():
    manager = EventManager()
    listener = DummyModuleListener()

    manager.subscribe(listener=listener)
    event = ModuleExecutedEvent("test")
    assert manager._listeners[type(event)] == [listener]
    manager.notify(event)
    assert listener.last_event is not None, "Listener was not notified"
    assert listener.last_event.module_id == "test", "Something went wrong when notifying the listener"

def test_event_listener_update_wrong_type():
    listener = DummyListener()
    with pytest.raises(TypeError):
        listener.update(DummyEvent())

def test_unsubscribe_never_subscribed():
    manager = EventManager()
    listener = DummyListener()
    with pytest.raises(ValueError):
        manager.unsubscribe(listener=listener)

def test_pipe_error_listener():
    manager = EventManager()
    error_listener = DummyErrorListener()
    manager.subscribe(listener=error_listener)
    pipeline = Pipeline()
    pipeline.add_module(DummyErrorModule)
    pipeline.event_manager = manager
    print(manager._listeners)
    pipeline.run()
    assert error_listener.last_event is not None, "Listener was not notified"
    assert error_listener.last_event.error_name == "test", "Something went wrong when notifying the listener"
    assert error_listener.last_event.error_msg == "test", "Something went wrong when notifying the listener"

