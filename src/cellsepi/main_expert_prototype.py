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
        self.modules = {} #identiefierer is the module_id
        self.width = BUILDER_WIDTH
        self.height = BUILDER_HEIGHT
        self.source_module: str = ""
        self.show_ports:bool = False
        self.show_delete_button:bool = False
        self.transmitting_ports: List[str] = []
        self.lines_gui = LinesGUI(self)
        self.controls.append(self.lines_gui)
        self.delete_stack = ft.Stack(width=self.width, height=self.height)
        self.controls.append(self.delete_stack)
        self.expand = True

    def add_connection(self,source_module_gui,target_module_gui,ports: List[str]):
        self.pipeline.add_connection(pipe=Pipe(source_module_gui.module, target_module_gui.module, ports))
        self.lines_gui.update_line(source_module_gui, target_module_gui,ports)
        target_module_gui.update_port_icons()

    def remove_connection(self,source_module_gui,target_module_gui):
        self.pipeline.remove_connection(source_module_gui.name,target_module_gui.name)
        self.lines_gui.remove_line(source_module_gui, target_module_gui)
        self.check_for_valid()
        target_module_gui.update_port_icons()

    def add_module(self,module_type: ModuleType,x: float = None,y: float = None):
        module_gui = ModuleGUI(self,module_type,x,y)
        self.controls.append(module_gui)
        self.update()
        return module_gui

    def set_in_background(self, module_gui:ModuleGUI):
        """
        Move a Module from it current position in the stack to the deepest intended level.
        """
        if module_gui in self.controls:
            self.controls.remove(module_gui)
            self.controls.insert(2, module_gui)
            self.update()

    def set_in_foreground(self, module_gui:ModuleGUI):
        """
        Move a Module from it current position in the stack to the highest level.
        """
        for module in self.modules.values():
            if module.name != module_gui.name:
                self.set_in_background(module)

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
                if all(k in target_module_gui.module.inputs for k in self.transmitting_ports) and self.transmitting_ports != [] and not self.pipeline.check_connections(self.source_module, target_module_gui.name) and not(self.pipeline.check_ports_occupied(target_module_gui.name, self.transmitting_ports)):
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

def calc_line_point_outside_module(pixels:List[int], module_x, module_y,target:bool=False):
    min_x = module_x - (MODULE_WIDTH / 2 + ARROW_PADDING)
    max_x = module_x + (MODULE_WIDTH / 2 + ARROW_PADDING)
    min_y = module_y - (MODULE_HEIGHT / 2 + ARROW_PADDING)
    max_y = module_y + (MODULE_HEIGHT / 2 + ARROW_PADDING)

    pixels_list = reversed(pixels) if target else pixels
    for x,y in pixels_list:
        if x < min_x or x > max_x or y < min_y or y > max_y:
            return x,y
    return module_x,module_y

def calc_mid_outside(pixels:List[int],source_x, source_y,target_x, target_y):
    start_point_x,start_point_y = calc_line_point_outside_module(pixels,source_x,source_y,False)
    end_point_x,end_point_y = calc_line_point_outside_module(pixels,target_x,target_y,True)
    return (start_point_x+end_point_x)/2, (start_point_y + end_point_y)/2

class LinesGUI(canvas.Canvas):
    def __init__(self, pipeline_gui: PipelineGUI):
        super().__init__()
        self.shapes = []
        self.edges = {} #identiefier Tuple of source name and target name
        self.arrows = {} #identiefier Tuple of source name and target name
        self.ports_txt = {} #identiefier Tuple of source name and target name
        self.delete_buttons = {} #identiefier Tuple of source name and target name
        self.pipeline_gui = pipeline_gui
        self.width = BUILDER_WIDTH
        self.height = BUILDER_HEIGHT
        self.expand = True

    def update_line(self,source_module_gui: ModuleGUI ,target_module_gui: ModuleGUI,ports: List[str]):
        """
        Adds a line between two modules or updates them if it already exists.
        """
        if (source_module_gui.name,target_module_gui.name) in self.edges:
            self.shapes.remove(self.edges[(source_module_gui.name,target_module_gui.name)])
            self.shapes.remove(self.arrows[(source_module_gui.name,target_module_gui.name)])
            self.shapes.remove(self.ports_txt[(source_module_gui.name,target_module_gui.name)])
            self.pipeline_gui.delete_stack.controls.remove(self.delete_buttons.pop((source_module_gui.name, target_module_gui.name)))

        source_x = source_module_gui.left + (MODULE_WIDTH / 2)
        source_y = source_module_gui.top + (MODULE_HEIGHT / 2)
        target_x = target_module_gui.left + (MODULE_WIDTH / 2)
        target_y = target_module_gui.top+ (MODULE_HEIGHT / 2)
        edge = canvas.Line(
            x1=source_x, y1=source_y,
            x2=target_x, y2=target_y,
            paint=ft.Paint(stroke_width=3, color=ARROW_COLOR)
        )
        edge_angle = calc_angle(source_x,source_y,target_x,target_y)

        pixels_edge = bresenham_line(QPointF(source_x,source_y), QPointF(target_x,target_y))



        arrow_x,arrow_y = calc_line_point_outside_module(pixels_edge, target_x, target_y,True)

        port_x,port_y = calc_mid_outside(pixels_edge, source_x, source_y,target_x, target_y)



        arrow_line_x1 = arrow_x - ARROW_LENGTH * math.cos(edge_angle - ARROW_ANGLE)
        arrow_line_y1 = arrow_y - ARROW_LENGTH * math.sin(edge_angle - ARROW_ANGLE)

        arrow_line_x2 = arrow_x - ARROW_LENGTH * math.cos(edge_angle + ARROW_ANGLE)
        arrow_line_y2 = arrow_y - ARROW_LENGTH * math.sin(edge_angle + ARROW_ANGLE)

        arrow = canvas.Path(
                [
                    canvas.Path.MoveTo(arrow_x,arrow_y),
                    canvas.Path.LineTo(arrow_line_x1,arrow_line_y1),
                    canvas.Path.LineTo(arrow_line_x2, arrow_line_y2),
                    canvas.Path.Close()
                ],
                paint=ft.Paint(
                    style=ft.PaintingStyle.FILL,color=ARROW_COLOR
                ),
            )

        port_str = ", ".join(ports)

        port_txt = canvas.Text(
            port_x,port_y,
            str(port_str),max_width=220, style=ft.TextStyle(size=15,weight=ft.FontWeight.BOLD,bgcolor=ft.Colors.WHITE38),
            alignment=ft.alignment.center,visible=self.pipeline_gui.show_ports
        )

        def dummy():
            pass
        delete_button = ft.GestureDetector(top=port_y-20,left=port_x-20,on_hover=lambda e:dummy(),content=ft.IconButton(
            icon=ft.Icons.CLOSE,tooltip="Delete Connection",hover_color=VALID_COLOR,icon_color=ft.Colors.WHITE,bgcolor=ft.Colors.RED_ACCENT,on_click=lambda e,source=source_module_gui,target=target_module_gui:self.pipeline_gui.remove_connection(source,target)
            ),visible=self.pipeline_gui.show_delete_button)

        self.shapes.append(edge)
        self.shapes.append(arrow)
        self.shapes.append(port_txt)
        self.pipeline_gui.delete_stack.controls.append(delete_button)
        self.edges[(source_module_gui.name,target_module_gui.name)] = edge
        self.arrows[(source_module_gui.name,target_module_gui.name)] = arrow
        self.ports_txt[(source_module_gui.name,target_module_gui.name)] = port_txt
        self.delete_buttons[(source_module_gui.name,target_module_gui.name)] = delete_button
        self.update()
        self.pipeline_gui.delete_stack.update()


    def remove_line(self, source_module_gui: ModuleGUI, target_module_gui: ModuleGUI):
        """
        Removes a line between two modules.
        """
        if (source_module_gui.name, target_module_gui.name) in self.edges:
            self.shapes.remove(self.edges.pop((source_module_gui.name, target_module_gui.name)))
            self.shapes.remove(self.arrows.pop((source_module_gui.name, target_module_gui.name)))
            self.shapes.remove(self.ports_txt.pop((source_module_gui.name, target_module_gui.name)))
            self.pipeline_gui.delete_stack.controls.remove(self.delete_buttons.pop((source_module_gui.name, target_module_gui.name)))
            self.update()
            self.pipeline_gui.delete_stack.update()

    def update_lines(self,module_gui: ModuleGUI):
        """
        Updates all lines that are connected to the given module.
        """
        for pipe in self.pipeline_gui.pipeline.pipes_in[module_gui.module.module_id]:
            self.update_line(self.pipeline_gui.modules[pipe.source_module.module_id],module_gui,pipe.ports)
        for pipe in self.pipeline_gui.pipeline.pipes_out[module_gui.module.module_id]:
            self.update_line(module_gui,self.pipeline_gui.modules[pipe.target_module.module_id],pipe.ports)

    def update_all(self):
        for module in self.pipeline_gui.modules.values():
            self.update_lines(module)

class Builder:
    def __init__(self,page: ft.Page):
        self.page = page
        self.pipeline_gui = PipelineGUI()
        self.add_module = AddModule(self)
        self.setup()
        self.old_show_ports = False

    def delete_button(self):
        #for module in self.pipeline_gui.modules.values():
        #    print(module.name,module.left,module.top)
        if self.pipeline_gui.show_delete_button:
            self.pipeline_gui.show_delete_button = False
            self.pipeline_gui.show_ports = self.old_show_ports
            self.pipeline_gui.lines_gui.update_all()
        else:
            self.old_show_ports = self.pipeline_gui.show_ports
            self.pipeline_gui.show_delete_button = True
            self.pipeline_gui.show_ports = False
            self.pipeline_gui.lines_gui.update_all()

    def setup(self):
        self.page.add(
            ft.Column([
                self.pipeline_gui,
                self.add_module,
                ft.IconButton(icon=ft.Icons.DELETE,on_click=lambda e: self.delete_button()),
             ]
            )
        )

def main(page: ft.Page):
    builder = Builder(page)
    pipeline_gui = builder.pipeline_gui
    module_gui1 = pipeline_gui.add_module(ModuleType.READ_LIF_TIF,491.0,262.0)
    module_gui2 = pipeline_gui.add_module(ModuleType.BATCH_IMAGE_SEG,60.0,259.0)
    module_gui3 = pipeline_gui.add_module(ModuleType.BATCH_IMAGE_READOUT,66.0,33.0)
    module_gui4 = pipeline_gui.add_module(ModuleType.BATCH_IMAGE_READOUT,351.0,30.0)
    pipeline_gui.add_connection(module_gui1,module_gui2,["image_paths","mask_paths"])
    pipeline_gui.add_connection(module_gui2,module_gui3,["mask_paths"])
    pipeline_gui.add_connection(module_gui2, module_gui4, ["mask_paths"])
    pipeline_gui.add_connection(module_gui1, module_gui4, ["image_paths"])

ft.app(main)
