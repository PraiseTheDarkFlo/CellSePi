from enum import Enum
from typing import List, Tuple

import flet as ft
import flet.canvas as canvas

from cellsepi.gui_module import ModuleGUI
from cellsepi.add_module import AddModule
from cellsepi.backend.main_window.expert_mode.modules.batch_image_readout import BatchImageReadoutModule
from cellsepi.backend.main_window.expert_mode.modules.batch_image_seg import BatchImageSegModule
from cellsepi.backend.main_window.expert_mode.modules.read_lif_tif import ReadLifTif
from cellsepi.backend.main_window.expert_mode.pipe import Pipe
from cellsepi.backend.main_window.expert_mode.pipeline import Pipeline
from cellsepi.expert_constants import *



class PipelineGUI(ft.Stack):
    def __init__(self):
        super().__init__()
        self.controls = []
        self.pipeline = Pipeline()
        self.lines_gui = LinesGUI(self)
        self.modules = {} #identiefierer is the module_id
        self.width = BUILDER_WIDTH
        self.height = BUILDER_HEIGHT
        self.source_module: str = ""
        self.transmitting_ports: List[str] = []
        self.controls.append(self.lines_gui)

    def add_connection(self,source_module_gui,target_module_gui,ports: List[str]):
        self.pipeline.add_connection(pipe=Pipe(source_module_gui.module, target_module_gui.module, ports))
        self.lines_gui.update_line(source_module_gui, target_module_gui)

    def remove_connection(self,source_module_gui,target_module_gui):
        self.pipeline.remove_connection(source_module_gui.name,target_module_gui.name)
        self.lines_gui.remove_line(source_module_gui, target_module_gui)

    def add_module(self,module_type: ModuleType):
        module_gui = ModuleGUI(self,module_type)
        self.controls.append(module_gui)
        self.update()
        return module_gui

    def remove_module(self,module_id: str):
        self.pipeline.remove_module(self.modules[module_id].module)
        self.controls.remove(self.modules.pop(module_id))
        self.update()

    def toggle_all_module_detection(self,module_id: str):
        self.source_module = module_id
        self.transmitting_ports = []
        for module in self.modules.values():
            if module.name != module_id:
                module.toggle_detection()
                self.update()

    def check_for_valid(self):
        for target_module_gui in self.modules.values():
            if target_module_gui.name != self.source_module:
                if all(k in target_module_gui.module.inputs for k in self.transmitting_ports) and self.transmitting_ports != [] and not self.pipeline.check_connections(self.source_module, target_module_gui.name):
                    target_module_gui.set_valid()
                else:
                    target_module_gui.set_invalid()

class LinesGUI(canvas.Canvas):
    def __init__(self, pipeline_gui: PipelineGUI):
        super().__init__()
        self.shapes = []
        self.edges = {} #identiefier Tuple of source name and target name
        self.pipeline_gui = pipeline_gui
        self.width = BUILDER_WIDTH
        self.height = BUILDER_HEIGHT

    def update_line(self,source_module_gui: ModuleGUI ,target_module_gui: ModuleGUI):
        """
        Adds a line between two modules or updates them if it already exists.
        """
        if (source_module_gui.name,target_module_gui.name) in self.edges:
            self.shapes.remove(self.edges[(source_module_gui.name,target_module_gui.name)])

        edge = canvas.Line(
            x1=source_module_gui.left + (MODULE_WIDTH / 2), y1=source_module_gui.top + (MODULE_HEIGHT / 2),
            x2=target_module_gui.left + (MODULE_WIDTH / 2), y2=target_module_gui.top+ (MODULE_HEIGHT / 2),
            paint=ft.Paint(stroke_width=3, color="black")
        )
        self.shapes.append(edge)
        self.edges[(source_module_gui.name,target_module_gui.name)] = edge
        self.update()

    def remove_line(self, source_module_gui: ModuleGUI, target_module_gui: ModuleGUI):
        """
        Removes a line between two modules.
        """
        if (source_module_gui.name, target_module_gui.name) in self.edges:
            self.shapes.remove(self.edges.pop((source_module_gui.name, target_module_gui.name)))
            self.update()

    def update_lines(self,module_gui: ModuleGUI):
        """
        Updates all lines that are connected to the given module.
        """
        for pipe in self.pipeline_gui.pipeline.pipes_in[module_gui.module.module_id]:
            self.update_line(self.pipeline_gui.modules[pipe.source_module.module_id],module_gui)
        for pipe in self.pipeline_gui.pipeline.pipes_out[module_gui.module.module_id]:
            self.update_line(module_gui,self.pipeline_gui.modules[pipe.target_module.module_id])

class Builder:
    def __init__(self,page: ft.Page):
        self.page = page
        self.pipeline_gui = PipelineGUI()
        self.add_module = AddModule(self)
        self.setup()

    def setup(self):
        self.page.add(
            ft.Column(
             [self.pipeline_gui,
                self.add_module,
             ]
            )
        )

def main(page: ft.Page):
    builder = Builder(page)
    pipeline_gui = builder.pipeline_gui
    module_gui1 = pipeline_gui.add_module(ModuleType.READ_LIF_TIF)
    module_gui2 = pipeline_gui.add_module(ModuleType.BATCH_IMAGE_SEG)
    module_gui3 = pipeline_gui.add_module(ModuleType.BATCH_IMAGE_READOUT)
    module_gui4 = pipeline_gui.add_module(ModuleType.BATCH_IMAGE_READOUT)
    pipeline_gui.add_connection(module_gui1,module_gui2,["image_paths","mask_paths"])
    pipeline_gui.add_connection(module_gui2,module_gui3,["mask_paths"])
    pipeline_gui.add_connection(module_gui2, module_gui4, ["mask_paths"])
    pipeline_gui.add_connection(module_gui1, module_gui4, ["image_paths"])

ft.app(main)
