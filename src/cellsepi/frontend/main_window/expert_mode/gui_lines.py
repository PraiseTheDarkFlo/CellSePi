import math
import threading

import flet as ft
from typing import List

from flet_core import canvas

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

def calc_line_point_outside_module(source_x, source_y, target_x, target_y, padding: float = 0):
    def rect_sides(x, y):
        w = MODULE_WIDTH / 2 + padding
        h = MODULE_HEIGHT / 2 + padding
        return x - w, x + w, y - h, y + h

    def intersect_line_rect(x1, y1, x2, y2, xmin, xmax, ymin, ymax):
        dx = x2 - x1
        dy = y2 - y1
        points = []

        if dx != 0:
            t = (xmin - x1) / dx
            y = y1 + t * dy
            if ymin <= y <= ymax:
                points.append((xmin, y))

            t = (xmax - x1) / dx
            y = y1 + t * dy
            if ymin <= y <= ymax:
                points.append((xmax, y))

        if dy != 0:
            t = (ymin - y1) / dy
            x = x1 + t * dx
            if xmin <= x <= xmax:
                points.append((x, ymin))

            t = (ymax - y1) / dy
            x = x1 + t * dx
            if xmin <= x <= xmax:
                points.append((x, ymax))

        if not points:
            return 0, 0
        points.sort(key=lambda p: (p[0]-x1)**2 + (p[1]-y1)**2)
        return points[0]

    t_xmin, t_xmax, t_ymin, t_ymax = rect_sides(target_x, target_y)
    s_xmin, s_xmax, s_ymin, s_ymax = rect_sides(source_x, source_y)

    target_point = intersect_line_rect(source_x, source_y, target_x, target_y, t_xmin, t_xmax, t_ymin, t_ymax)
    source_point = intersect_line_rect(target_x, target_y, source_x, source_y, s_xmin, s_xmax, s_ymin, s_ymax)

    return target_point, source_point


def calc_mid_outside(start_point_x,start_point_y,arrow_end_x, arrow_end_y):
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
        self._lock = threading.Lock()

    def update_line(self,source_module_gui: ModuleGUI ,target_module_gui: ModuleGUI,ports: List[str]):
        """
        Adds a line between two modules or updates them if it already exists.
        """
        key = (source_module_gui.name, target_module_gui.name)
        if key in self.edges and self.edges[key] in self.shapes:
            self.shapes.remove(self.edges[key])
        if key in self.arrows and self.arrows[key] in self.shapes:
            self.shapes.remove(self.arrows[key])
        if key in self.ports_txt and self.ports_txt[key] in self.shapes:
            self.shapes.remove(self.ports_txt[key])

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

        (target_x_outside,target_y_outside),(source_x_outside,source_y_outside) = calc_line_point_outside_module(source_x,source_y, target_x, target_y,padding=ARROW_PADDING)

        arrow_line_x1 = target_x_outside - ARROW_LENGTH * math.cos(edge_angle - ARROW_ANGLE)
        arrow_line_y1 = target_y_outside - ARROW_LENGTH * math.sin(edge_angle - ARROW_ANGLE)

        arrow_line_x2 = target_x_outside - ARROW_LENGTH * math.cos(edge_angle + ARROW_ANGLE)
        arrow_line_y2 = target_y_outside - ARROW_LENGTH * math.sin(edge_angle + ARROW_ANGLE)

        arrow_end_x = (arrow_line_x1 + arrow_line_x2)/2 #End is the Flat side of the Arrow
        arrow_end_y = (arrow_line_y1 + arrow_line_y2)/2
        port_x,port_y = calc_mid_outside(source_x_outside, source_y_outside,arrow_end_x, arrow_end_y)

        arrow = canvas.Path(
                [
                    canvas.Path.MoveTo(target_x_outside,target_y_outside),
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

    def update_lines_with_lock(self, module_gui):
        with self._lock:
            self.update_lines(module_gui)

    def update_all(self):
        for module in self.pipeline_gui.modules.values():
            self.update_lines(module)