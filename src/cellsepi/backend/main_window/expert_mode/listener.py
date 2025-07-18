from abc import ABC, abstractmethod
from typing import List, Type, TypeVar, Generic

class Event(ABC):
    """
    Abstract base class for all event types.
    Subclass this to define specific event types.
    """
    pass

class ProgressEvent(Event):
    def __init__(self,percent: int,process: str):
        self.percent = percent
        self.process = process

    def __str__(self):
        return f"ProgressEvent: {self.percent}% - {self.process}"

class ModuleEvent(Event):
    def __init__(self,module_name: str):
        self.module_name = module_name

class ErrorEvent(Event):
    def __init__(self,error_name: str, error_msg: str):
        self.error_name = error_name
        self.error_msg = error_msg

class EventListener(ABC):
    """
    Abstract base class for event listeners.
    Subclasses must define the type of event they handle and implement the update logic.
    """
    @abstractmethod
    def get_event_type(self) -> Type[Event]:
        pass

    def update(self, event: Event) -> None:
        if not isinstance(event, self.get_event_type()):
            raise TypeError("The given event is not the right event type!")
        self._update(event)

    @abstractmethod
    def _update(self, event: Event) -> None:
        pass
