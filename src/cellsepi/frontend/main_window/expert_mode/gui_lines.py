import math
import flet as ft
from typing import List

from PyQt5.QtCore import QPointF
from flet_core import canvas

from cellsepi.backend.drawing_window.drawing_util import bresenham_line
from cellsepi.frontend.main_window.expert_mode.expert_constants import MODULE_WIDTH, ARROW_PADDING, MODULE_HEIGHT, BUILDER_WIDTH, BUILDER_HEIGHT, \
    ARROW_COLOR, ARROW_LENGTH, ARROW_ANGLE, VALID_COLOR
from cellsepi.frontend.main_window.expert_mode.gui_module import ModuleGUI


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

def calc_mid_outside(pixels:List[int],source_x, source_y,arrow_end_x, arrow_end_y):
    start_point_x,start_point_y = calc_line_point_outside_module(pixels,source_x,source_y,False)
    return (start_point_x+arrow_end_x)/2, (start_point_y + arrow_end_y)/2

class LinesGUI(canvas.Canvas):
    def __init__(self, pipeline_gui):
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

        arrow_line_x1 = arrow_x - ARROW_LENGTH * math.cos(edge_angle - ARROW_ANGLE)
        arrow_line_y1 = arrow_y - ARROW_LENGTH * math.sin(edge_angle - ARROW_ANGLE)

        arrow_line_x2 = arrow_x - ARROW_LENGTH * math.cos(edge_angle + ARROW_ANGLE)
        arrow_line_y2 = arrow_y - ARROW_LENGTH * math.sin(edge_angle + ARROW_ANGLE)

        arrow_end_x = (arrow_line_x1 + arrow_line_x2)/2 #End is the Flat side of the Arrow
        arrow_end_y = (arrow_line_y1 + arrow_line_y2)/2
        port_x,port_y = calc_mid_outside(pixels_edge, source_x, source_y,arrow_end_x, arrow_end_y)

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
        disabled = False
        opacity = 1
        if (source_module_gui.name in self.pipeline_gui.pipeline.run_order or target_module_gui.name in self.pipeline_gui.pipeline.run_order or source_module_gui.name == self.pipeline_gui.pipeline.executing or target_module_gui.name == self.pipeline_gui.pipeline.executing) and self.pipeline_gui.pipeline.running:
            disabled = True
            opacity = 0.4
        delete_button = ft.GestureDetector(top=port_y-20,left=port_x-20,on_hover=lambda e:dummy(),content=ft.IconButton(
            icon=ft.Icons.CLOSE,tooltip="Delete Connection",hover_color=VALID_COLOR,icon_color=ft.Colors.WHITE,bgcolor=ft.Colors.RED_ACCENT,opacity=opacity,on_click=lambda e,source=source_module_gui,target=target_module_gui:self.pipeline_gui.remove_connection(source,target)
            ),visible=self.pipeline_gui.show_delete_button,disabled=disabled)

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

    def update_delete_button(self,source_module_gui: ModuleGUI, target_module_gui: ModuleGUI,set_all: bool = False):
        disabled = False
        opacity = 1
        if ((source_module_gui.name in self.pipeline_gui.pipeline.run_order or target_module_gui.name in self.pipeline_gui.pipeline.run_order or source_module_gui.name == self.pipeline_gui.pipeline.executing or target_module_gui.name == self.pipeline_gui.pipeline.executing) and self.pipeline_gui.pipeline.running) or set_all:
            disabled = True
            opacity = 0.4
        self.delete_buttons[(source_module_gui.name,target_module_gui.name)].content.opacity = opacity
        self.delete_buttons[(source_module_gui.name, target_module_gui.name)].content.disabled = disabled
        self.delete_buttons[(source_module_gui.name,target_module_gui.name)].content.update()

    def update_delete_buttons(self,module_gui: ModuleGUI,set_all: bool = False):
        """
        Updates all delete buttons that are connected to the given module.
        """
        for pipe in self.pipeline_gui.pipeline.pipes_in[module_gui.module.module_id]:
            self.update_delete_button(self.pipeline_gui.modules[pipe.source_module.module_id], module_gui,set_all)
        for pipe in self.pipeline_gui.pipeline.pipes_out[module_gui.module.module_id]:
            self.update_delete_button(module_gui, self.pipeline_gui.modules[pipe.target_module.module_id],set_all)

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