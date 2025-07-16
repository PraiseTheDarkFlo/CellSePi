from abc import ABC, abstractmethod
from typing import List, Type, TypeVar, Generic

class Event(ABC):
    """
    Abstract base class for all event types.
    Subclass this to define specific event types.
    """
    pass

class ProgressEvent(Event):
    def __init__(self,percent: float,name: str):
        self.percent = percent
        self.name = name


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
