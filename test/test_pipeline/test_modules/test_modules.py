from os import path
from typing import Type

import pytest

from cellsepi.backend.main_window.expert_mode import pipe
from cellsepi.backend.main_window.expert_mode.listener import EventListener, ProgressEvent, Event
from cellsepi.backend.main_window.expert_mode.modules.batch_image_readout import BatchImageReadoutModule
from cellsepi.backend.main_window.expert_mode.modules.batch_image_seg import BatchImageSegModule
from cellsepi.backend.main_window.expert_mode.modules.read_lif_tif import ReadLifTif
from cellsepi.backend.main_window.expert_mode.pipe import Pipe
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

def test_running_module_batch_image_seg():
    pipeline = Pipeline()
    pipeline.event_manager.subscribe(ReadLifTifListener())
    mod1 = pipeline.add_module(ReadLifTif)
    mod1._directory_path = "/home/mmdark/Downloads/data (3)/data/HEK293_mTagBFP_mNeonGreen_CellMaskDR_01.lif"
    mod1._lif = True
    mod2 = pipeline.add_module(BatchImageSegModule)
    mod2.model_path = "/home/mmdark/PycharmProjects/CellSePi/src/cellsepi/models/CP_20240715_171241"
    pipe1to2 = Pipe(mod1,mod2,["image_paths","mask_paths"])
    pipeline.add_connection(pipe1to2)
    pipeline.run()
    print(f"outputs{mod2.outputs["mask_paths"].data}")

def test_running_module_batch_image_readout():
    pipeline = Pipeline()
    pipeline.event_manager.subscribe(ReadLifTifListener())
    mod1 = pipeline.add_module(ReadLifTif)
    mod1._directory_path = "/home/mmdark/Downloads/data (3)/data/HEK293_mTagBFP_mNeonGreen_CellMaskDR_01.lif"
    mod1._lif = True
    mod2 = pipeline.add_module(BatchImageSegModule)
    mod2._model_path = "/home/mmdark/PycharmProjects/CellSePi/src/cellsepi/models/CP_20240715_171241"
    pipe1to2 = Pipe(mod1,mod2,["image_paths","mask_paths"])
    pipeline.add_connection(pipe1to2)
    mod3 = pipeline.add_module(BatchImageReadoutModule)
    mod3._directory_path = "/home/mmdark/Downloads/data (3)/data/"
    pipe1to3 = Pipe(mod1,mod3,["image_paths"])
    pipe2to3 = Pipe(mod2,mod3,["mask_paths"])
    pipeline.add_connection(pipe1to3)
    pipeline.add_connection(pipe2to3)
    pipeline.run()
    print(f"outputs{mod3.inputs["mask_paths"].data}")
