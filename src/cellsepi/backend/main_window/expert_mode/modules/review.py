import os

import numpy as np
from cv2 import imread
from tifffile import tifffile
from PIL import Image

from cellsepi.backend.main_window.data_util import load_directory, ReturnTypePath
from cellsepi.backend.main_window.expert_mode.listener import ProgressEvent
from cellsepi.backend.main_window.expert_mode.module import *
from cellsepi.backend.main_window.images import BatchImageSegmentation
from cellsepi.frontend.main_window.gui_directory import DirectoryCard


class Review(Module, ABC):
    _gui_config = ModuleGuiConfig("Review",Categories.MANUAL,"This module allows you to manually review the given masks.")
    def __init__(self, module_id: str) -> None:
        self._module_id = module_id
        self._event_manager: EventManager = None
        self._inputs = {
            "image_paths": Port("image_paths", dict), #dict[str,dict[str,str]],
            "mask_paths": Port("mask_paths", dict), #dict[str,dict[str,str]]
        }
        self._outputs = {
            #"mask_paths": Port("mask_paths", dict), #dict[str,dict[str,str]] when i allow editing
        }
        spacing = 10
        padding = 20
        self._settings: ft.Stack = ft.Stack([ft.Row([ft.Column([ft.Card(
                content=ft.Column(
                    [ft.Container(ft.ListView(
                        controls=[ft.Text("test")],
                        width=500,
                        spacing=spacing,
                    ),padding=padding)]
                )
            )],
                    alignment=ft.MainAxisAlignment.CENTER,)],alignment=ft.MainAxisAlignment.CENTER),])
        self.user_3d_on: bool = False


    @classmethod
    def gui_config(cls) -> ModuleGuiConfig:
       return cls._gui_config

    @property
    def module_id(self) -> str:
        return self._module_id

    @module_id.setter
    def module_id(self,value: str):
        self._module_id = value

    @property
    def inputs(self) -> dict[str, Port]:
        return self._inputs

    @property
    def outputs(self) -> dict[str, Port]:
        return self._outputs

    @property
    def settings(self) -> ft.Stack:
        return self._settings

    @property
    def event_manager(self) -> EventManager:
        return self._event_manager

    @event_manager.setter
    def event_manager(self, value: EventManager):
        self._event_manager = value

    def run(self):
        return True




