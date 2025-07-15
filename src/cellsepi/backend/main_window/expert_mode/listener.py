from abc import ABC, abstractmethod
from typing import List, Type, TypeVar, Generic

class Event(ABC):
    pass

class ProgressEvent(Event):
    def __init__(self,percent: float,name: str):
        self.percent = percent
        self.name = name


class EventListener(ABC):
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
