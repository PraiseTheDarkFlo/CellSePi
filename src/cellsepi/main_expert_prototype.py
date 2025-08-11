import math
from enum import Enum
from typing import List, Tuple

import flet as ft
import flet.canvas as canvas
from PyQt5.QtCore import QPointF

from cellsepi.backend.drawing_window.drawing_util import bresenham_line
from cellsepi.gui_module import ModuleGUI
from cellsepi.add_module import AddModule
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

def calc_angle(x1, y1, x2, y2):
    """
    Calculate the angle between two points in radiant.
    """
    delta_x = x2 - x1
    delta_y = y2 - y1
    return math.atan2(delta_y, delta_x)

def calc_start_point_arrow(pixels:List[int],target_x,target_y):
    min_x = target_x-(MODULE_WIDTH/2+ARROW_PADDING)
    max_x = target_x+(MODULE_WIDTH/2+ARROW_PADDING)
    min_y = target_y-(MODULE_HEIGHT/2+ARROW_PADDING)
    max_y = target_y+(MODULE_HEIGHT/2+ARROW_PADDING)
    for x,y in reversed(pixels):
        if x < min_x or x > max_x or y < min_y or y > max_y:
            return x,y
    return target_x,target_y

class LinesGUI(canvas.Canvas):
    def __init__(self, pipeline_gui: PipelineGUI):
        super().__init__()
        self.shapes = []
        self.edges = {} #identiefier Tuple of source name and target name
        self.arrows = {} #identiefier Tuple of source name and target name
        self.pipeline_gui = pipeline_gui
        self.width = BUILDER_WIDTH
        self.height = BUILDER_HEIGHT

    def update_line(self,source_module_gui: ModuleGUI ,target_module_gui: ModuleGUI):
        """
        Adds a line between two modules or updates them if it already exists.
        """
        if (source_module_gui.name,target_module_gui.name) in self.edges:
            self.shapes.remove(self.edges[(source_module_gui.name,target_module_gui.name)])
            self.shapes.remove(self.arrows[(source_module_gui.name,target_module_gui.name)])

        source_x = source_module_gui.left + (MODULE_WIDTH / 2)
        source_y = source_module_gui.top + (MODULE_HEIGHT / 2)
        target_x = target_module_gui.left + (MODULE_WIDTH / 2)
        target_y = target_module_gui.top+ (MODULE_HEIGHT / 2)
        edge = canvas.Line(
            x1=source_x, y1=source_y,
            x2=target_x, y2=target_y,
            paint=ft.Paint(stroke_width=3, color="black")
        )
        edge_angle = calc_angle(source_x,source_y,target_x,target_y)

        pixels_edge = bresenham_line(QPointF(source_x,source_y), QPointF(target_x,target_y))



        arrow_x,arrow_y = calc_start_point_arrow(pixels_edge,target_x,target_y)

        arrow_line_x1 = arrow_x - ARROW_LENGTH * math.cos(edge_angle - ARROW_ANGLE)
        arrow_line_y1 = arrow_y - ARROW_LENGTH * math.sin(edge_angle - ARROW_ANGLE)

        arrow_line_x2 = arrow_x - ARROW_LENGTH * math.cos(edge_angle + ARROW_ANGLE)
        arrow_line_y2 = arrow_y - ARROW_LENGTH * math.sin(edge_angle + ARROW_ANGLE)

        arrow = canvas.Path(
                [
                    canvas.Path.MoveTo(arrow_x,arrow_y),
                    canvas.Path.LineTo(arrow_line_x1,arrow_line_y1),
                    canvas.Path.LineTo(arrow_line_x2, arrow_line_y2),
                ],
                paint=ft.Paint(
                    style=ft.PaintingStyle.FILL,
                ),
            )

        self.shapes.append(edge)
        self.shapes.append(arrow)
        self.edges[(source_module_gui.name,target_module_gui.name)] = edge
        self.arrows[(source_module_gui.name,target_module_gui.name)] = arrow
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
