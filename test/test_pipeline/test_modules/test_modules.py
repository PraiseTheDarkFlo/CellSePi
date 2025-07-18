from typing import Type

import pytest

from cellsepi.backend.main_window.expert_mode import pipe
from cellsepi.backend.main_window.expert_mode.listener import EventListener, ProgressEvent, Event
from cellsepi.backend.main_window.expert_mode.modules.read_lif_tif import ReadLifTif
from cellsepi.backend.main_window.expert_mode.pipeline import Pipeline

class ReadLifTifListener(EventListener):
    def __init__(self):
        self.event_type = ProgressEvent
    def get_event_type(self) -> Type[Event]:
        return self.event_type

    def update(self, event: Event) -> None:
        if not isinstance(event, self.get_event_type()):
            raise TypeError("The given event is not the right event type!")
        self._update(event)

    def _update(self, event: Event) -> None:
        print(event)


def test_running_module_read_lif():
    pipeline = Pipeline()
    pipeline.event_manager.subscribe(ReadLifTifListener())
    mod1 = pipeline.add_module(ReadLifTif)
    mod1._directory_path = "/home/mmdark/Downloads/data (3)/data/HEK293_mTagBFP_mNeonGreen_CellMaskDR_01.lif"
    mod1._lif = True
    pipeline.run()


def test_running_module_read_tif():
    pipeline = Pipeline()
    pipeline.event_manager.subscribe(ReadLifTifListener())
    mod1 = pipeline.add_module(ReadLifTif)
    mod1._directory_path = "/home/mmdark/Downloads/data (3)/data/04072024_HEK293_CellMaskDR_01"
    pipeline.run()