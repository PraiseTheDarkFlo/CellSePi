import math
from enum import Enum
from typing import List, Tuple

import flet as ft
import flet.canvas as canvas
from PyQt5.QtCore import QPointF
from flet_core.colors import WHITE60

from cellsepi.backend.drawing_window.drawing_util import bresenham_line
from cellsepi.frontend.main_window.gui_directory import format_directory_path
from cellsepi.gui_module import ModuleGUI
from cellsepi.backend.main_window.expert_mode.pipe import Pipe
from cellsepi.backend.main_window.expert_mode.pipeline import Pipeline
from cellsepi.expert_constants import *
from cellsepi.gui_pipeline_listener import PipelineChangeListener, ModuleExecutedListener, ModuleStartedListener, \
    ModuleProgressListener, ModuleErrorListener


class PipelineGUI(ft.Stack):
    def __init__(self,page:ft.Page):
        super().__init__()
        self.controls = []
        self.pipeline = Pipeline()
        self.modules_executed = 0
        self.module_running_count = 0
        self.page = page
        self.modules = {} #identiefierer is the module_id
        self.show_room_size = SHOWROOM_MODULE_COUNT*2+1
        self.show_room_modules = []
        self.width = BUILDER_WIDTH
        self.height = BUILDER_HEIGHT
        self.source_module: str = ""
        self.show_ports:bool = False
        self.show_delete_button:bool = False
        self.transmitting_ports: List[str] = []
        self.lines_gui = LinesGUI(self)
        self.controls.append(self.lines_gui)
        self.show_room_container = None
        self.show_room_page_number: int = 0
        self.show_room_max_page_number: int = 0
        self.page_stack = None
        self.delete_stack = ft.Stack()
        self.controls.append(self.delete_stack)
        self.expand = True
        self.offset_x = 0
        self.offset_y = 0
        self.save_dir = ""
        self.name = ""

    def save(self):
        pass

    def add_connection(self,source_module_gui,target_module_gui,ports: List[str]):
        ports_copy = list(ports)
        self.pipeline.add_connection(pipe=Pipe(source_module_gui.module, target_module_gui.module, ports_copy))
        self.lines_gui.update_line(source_module_gui, target_module_gui,ports)
        self.update_all_port_icons()

    def remove_connection(self,source_module_gui,target_module_gui):
        self.pipeline.remove_connection(source_module_gui.name,target_module_gui.name)
        self.lines_gui.remove_line(source_module_gui, target_module_gui)
        self.update_all_port_icons()
        self.check_for_valid_all_modules()

    def add_show_room_module(self,module_type:ModuleType,x:float,y:float,visible:bool=True):
        module_gui = ModuleGUI(self, module_type, x, y,True,visible)
        self.page_stack.controls.append(module_gui)
        return module_gui

    def refill_show_room(self,module_gui:ModuleGUI,visible:bool=True,index:int=None):
        new_module_gui = ModuleGUI(self, module_gui.module_type, x=SPACING_X + SHOWROOM_PADDING_X / 2, y=module_gui.show_offset_y, show_mode=True, visible=visible, index=index)
        self.page_stack.controls.append(new_module_gui)
        self.page_stack.update()
        self.update_all_port_icons()

    def build_show_room(self,page_stack:ft.Stack):
        self.page_stack = page_stack
        x = SPACING_X + SHOWROOM_PADDING_X / 2
        y = SPACING_Y
        self.show_room_container = ft.Container(top=y - SPACING_Y / 2, left=SPACING_X, width=MODULE_WIDTH + SHOWROOM_PADDING_X, height=(((self.show_room_size - 1) / 2) * MODULE_HEIGHT) + (((self.show_room_size - 1) / 2) * SPACING_Y), bgcolor=MENU_COLOR, border_radius=ft.border_radius.all(10),blur=10)
        self.page_stack.controls.append(self.show_room_container)
        self.show_room_max_page_number = math.ceil(len(ModuleType) / SHOWROOM_MODULE_COUNT)
        for i,module_type in enumerate(ModuleType):
            visible = i < SHOWROOM_MODULE_COUNT
            y_module = y+ (MODULE_HEIGHT + SPACING_Y) * (i%SHOWROOM_MODULE_COUNT)
            self.add_show_room_module(module_type,x,y_module,visible)
            self.add_show_room_module(module_type,x,y_module,visible)

    def change_page(self,page_number:int):
        self.show_room_page_number = page_number
        for i,module in enumerate(self.show_room_modules):
            module_page = (i//2) // SHOWROOM_MODULE_COUNT
            if module_page == self.show_room_page_number:
                module.visible = True
            else:
                module.visible = False
            module.update()

    def update_show_room(self):
        self.show_room_container.left = SPACING_X
        self.show_room_container.top = SPACING_Y - SPACING_Y / 2
        self.show_room_container.update()
        for module in self.show_room_modules:
            module.left = SPACING_X + SHOWROOM_PADDING_X / 2
            module.update()

    def add_module(self,module_type: ModuleType,x: float = None,y: float = None):
        module_gui = ModuleGUI(self,module_type,x,y)
        self.controls.append(module_gui)
        self.update()
        return module_gui

    def set_in_background(self, module_gui:ModuleGUI,behind_delete=False):
        """
        Move a Module from it current position in the stack to the deepest intended level.
        Attribute:
            behind_delete: if the module should be render behind the delete buttons.
        """
        if module_gui in self.controls:
            self.controls.remove(module_gui)
            if behind_delete:
                self.controls.insert(1, module_gui)
            else:
                self.controls.remove(self.delete_stack)
                self.controls.insert(1, self.delete_stack)
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

    def toggle_all_stuck_in_running(self):
        for module in self.pipeline.run_order:
            show_room_names = [m.name for m in self.show_room_modules]
            if module in show_room_names:
                continue
            self.lines_gui.update_delete_buttons(
                self.modules[module])
            self.modules[module].enable_tools()
            self.modules[module].start_button.visible = True
            self.modules[module].start_button.update()
            self.modules[module].delete_button.visible = True
            self.modules[module].delete_button.update()
            self.modules[module].pause_button.visible = False
            self.modules[module].pause_button.update()
            self.modules[module].waiting_button.visible = False
            self.modules[module].waiting_button.update()
        if self.pipeline.executing != "":
            self.lines_gui.update_delete_buttons(
                self.modules[self.pipeline.executing])
            self.modules[self.pipeline.executing].enable_tools()
            self.modules[self.pipeline.executing].start_button.visible = True
            self.modules[self.pipeline.executing].start_button.update()
            self.modules[self.pipeline.executing].delete_button.visible = True
            self.modules[self.pipeline.executing].delete_button.update()
            self.modules[self.pipeline.executing].pause_button.visible = False
            self.modules[self.pipeline.executing].pause_button.update()
            self.modules[self.pipeline.executing].waiting_button.visible = False
            self.modules[self.pipeline.executing].waiting_button.update()
        self.check_for_valid_all_modules()

    def check_for_valid_all_modules(self):
        for target_module_gui in self.modules.values():
            self.check_for_valid(target_module_gui.name)

    def check_for_valid(self,module_id: str):
        target_module_gui = self.modules[module_id]
        if (target_module_gui.name not in self.pipeline.run_order or not self.pipeline.running) and target_module_gui.name != self.pipeline.executing:
            if target_module_gui.name != self.source_module:
                if all(k in target_module_gui.module.inputs for k in
                       self.transmitting_ports) and self.transmitting_ports != [] and not self.pipeline.check_connections(
                        self.source_module, target_module_gui.name) and not (
                self.pipeline.check_ports_occupied(target_module_gui.name, self.transmitting_ports)):
                    target_module_gui.set_valid()
                else:
                    target_module_gui.set_invalid()

    def update_all_port_icons(self):
        for module_gui in self.modules.values():
            module_gui.update_port_icons()



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
        bgcolor = ft.Colors.RED_ACCENT
        if (source_module_gui.name in self.pipeline_gui.pipeline.run_order or target_module_gui.name in self.pipeline_gui.pipeline.run_order or source_module_gui.name == self.pipeline_gui.pipeline.executing or target_module_gui.name == self.pipeline_gui.pipeline.executing) and self.pipeline_gui.pipeline.running:
            disabled = True
            bgcolor = DISABLED_BUTTONS_COLOR
        delete_button = ft.GestureDetector(top=port_y-20,left=port_x-20,on_hover=lambda e:dummy(),content=ft.IconButton(
            icon=ft.Icons.CLOSE,tooltip="Delete Connection",hover_color=VALID_COLOR,icon_color=ft.Colors.WHITE,bgcolor=bgcolor,on_click=lambda e,source=source_module_gui,target=target_module_gui:self.pipeline_gui.remove_connection(source,target)
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
        bgcolor = ft.Colors.RED_ACCENT
        if ((source_module_gui.name in self.pipeline_gui.pipeline.run_order or target_module_gui.name in self.pipeline_gui.pipeline.run_order or source_module_gui.name == self.pipeline_gui.pipeline.executing or target_module_gui.name == self.pipeline_gui.pipeline.executing) and self.pipeline_gui.pipeline.running) or set_all:
            disabled = True
            bgcolor = DISABLED_BUTTONS_COLOR
        self.delete_buttons[(source_module_gui.name,target_module_gui.name)].content.bgcolor = bgcolor
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

class Builder:
    def __init__(self,page: ft.Page):
        self.page = page
        self.page_stack = None
        self.pipeline_gui = PipelineGUI(page)
        file_picker = ft.FilePicker(
            on_result=lambda a: self.on_select_file(a))
        self.pipeline_gui.page.overlay.extend([file_picker])
        self.load_button = ft.IconButton(icon=ft.Icons.UPLOAD_FILE, on_click=lambda e: file_picker.pick_files(allow_multiple=False),
                                         icon_color=WHITE60,
                                         style=ft.ButtonStyle(
                                             shape=ft.RoundedRectangleBorder(radius=12), ),
                                         tooltip="Load pipeline", hover_color=ft.Colors.WHITE12)

        self.save_menu_button = ft.IconButton(icon=ft.Icons.SAVE_ALT_SHARP, on_click=lambda e: self.save_button_click(),
                                              icon_color=WHITE60,
                                              style=ft.ButtonStyle(
                                               shape=ft.RoundedRectangleBorder(radius=12), ),
                                              tooltip="Save pipeline", hover_color=ft.Colors.WHITE12)
        self.run_menu_button = ft.IconButton(icon=ft.Icons.PLAY_ARROW, on_click=lambda e: self.run_menu_click(),
                                         icon_color=WHITE60,
                                         style=ft.ButtonStyle(
                                             shape=ft.RoundedRectangleBorder(radius=12), ),
                                         tooltip="Show run menu", hover_color=ft.Colors.WHITE12)
        ref = ft.Ref[ft.Text]()
        choose_name = ft.TextField(
            label="Pipeline name",
            border_color=ft.Colors.BLUE_ACCENT,
            value="",
            color=ft.Colors.WHITE60,
            ref=ref,
            on_blur=lambda e, reference=ref: self.on_change(e,reference),label_style=ft.TextStyle(color=ft.Colors.WHITE60),
            height=60,width=185
        )
        text_field = ft.TextField(
            label="Save directory",
            border_color=ft.Colors.WHITE60,
            value=None,
            height=60,
            color=ft.Colors.WHITE60,width=250,
            read_only=True,label_style=ft.TextStyle(color=ft.Colors.WHITE60),
        )
        dir_picker = ft.FilePicker(
            on_result=lambda a, text=text_field: self.on_select_dir(a,text))
        self.page.overlay.extend([dir_picker])
        directory_stack = ft.Stack([text_field, ft.Container(
            content=ft.IconButton(
                icon=ft.Icons.FOLDER_OPEN,icon_color=ft.Colors.WHITE60,
                tooltip="Choose directory",hover_color=ft.Colors.WHITE12,
                on_click=lambda e: dir_picker.get_directory_path(),
            ),
            alignment=ft.alignment.top_right, right=10, top=5
        )
        ])
        self.save_button = ft.ElevatedButton(  # button to start the pipeline
            text="Save",
            icon=ft.Icons.DOWNLOAD_FOR_OFFLINE_SHARP,
            tooltip="Save the pipeline",
            disabled=False,
            on_click=lambda e: self.pipeline_gui.save(),
            opacity=0.75
        )
        save_row = ft.Row([choose_name, self.save_button],tight=True,spacing=20)
        self.delete_button = ft.IconButton(icon=ft.Icons.DELETE,on_click=lambda e: self.delete_button_click(),icon_color=WHITE60,
                                                 style=ft.ButtonStyle(
                                              shape=ft.RoundedRectangleBorder(radius=12),),
                                                 tooltip="Show delete buttons", hover_color=ft.Colors.WHITE12)
        self.port_button = ft.IconButton(icon=ft.Icons.VISIBILITY, on_click=lambda e: self.port_button_click(),
                                           icon_color=WHITE60,
                                           style=ft.ButtonStyle(
                                               shape=ft.RoundedRectangleBorder(radius=12), ),
                                           tooltip="Show which ports get transferred", hover_color=ft.Colors.WHITE12)

        self.slider_horizontal = ft.Slider(min=0,max=1,height=40,on_change=lambda e: self.scroll_horizontal(e),active_color=ft.Colors.BLUE_400,inactive_color=WHITE60,overlay_color=ft.Colors.WHITE12)
        self.tools = ft.Container(ft.Container(ft.Column(
                [
                    self.load_button, self.save_menu_button,self.run_menu_button,self.delete_button,self.port_button
                ], tight=True,spacing=2
            ), bgcolor=MENU_COLOR, expand=True
            ),bgcolor=ft.Colors.TRANSPARENT,border_radius=ft.border_radius.all(10),
            bottom=20,left=SPACING_X,width=40,blur=10)
        self.save_menu = ft.Container(ft.Container(ft.Column(
                [
                    directory_stack,save_row,
                ], tight=True,spacing=2
            ), bgcolor=MENU_COLOR, expand=True,padding=20
            ),bgcolor=ft.Colors.TRANSPARENT,border_radius=ft.border_radius.all(10),width=0,height=150,
            bottom=20,left=self.tools.left+ self.tools.width + 5,blur=10,opacity=0,
            animate_opacity=ft.Animation(duration=300, curve=ft.AnimationCurve.LINEAR_TO_EASE_OUT),
            animate=ft.Animation(duration=300, curve=ft.AnimationCurve.LINEAR_TO_EASE_OUT),)
        self.start_button = ft.ElevatedButton(  # button to start the pipeline
            text="Start",
            icon=ft.Icons.PLAY_CIRCLE,
            tooltip="Start the pipeline",
            disabled=False,
            on_click=lambda e:self.run(),
            opacity=0.75
        )
        self.resume_button = ft.ElevatedButton(  # button to resume the pipeline
            text="Resume the pipeline",
            icon=ft.Icons.PLAY_CIRCLE,
            visible=False,
            on_click=self.pipeline_gui.pipeline.run(resume=True),
            opacity=0.75
        )
        self.progress_bar_module = ft.ProgressBar(value=0, width=220,bgcolor=ft.Colors.WHITE24,color=ft.Colors.BLUE_400)
        self.progress_pipeline = ft.ProgressRing(value=0,width=50,height=50,stroke_width=8,bgcolor=ft.Colors.WHITE24,color=ft.Colors.BLUE_400)
        self.progress_text = ft.Text(f"{self.pipeline_gui.modules_executed}/{len(self.pipeline_gui.pipeline.modules)}",weight=ft.FontWeight.BOLD,tooltip="How many modules has been executed",color=ft.Colors.WHITE60)
        self.progress_stack = ft.Stack([self.progress_pipeline,ft.Container(self.progress_text,alignment=ft.alignment.center)],width=50,height=50,)
        self.progress_bar_module_text = ft.Text("0%",color=ft.Colors.WHITE60)
        self.progress_and_start = ft.Column([ft.Container(self.progress_stack,alignment=ft.alignment.center),
            ft.Container(
                content=ft.Stack([self.start_button, self.resume_button]),alignment=ft.alignment.center)],width=85,spacing=20
        )
        self.running_module = ft.Text("Module",color=ft.Colors.WHITE60,width=230,overflow=ft.TextOverflow.ELLIPSIS,max_lines=1,style=ft.TextThemeStyle.HEADLINE_SMALL)
        self.info_text = ft.Text("Idle, waiting for start.",color=ft.Colors.WHITE60,width=250,overflow=ft.TextOverflow.ELLIPSIS,max_lines=2)
        self.category_icon = ft.Icon(ft.Icons.CATEGORY_ROUNDED,color=ft.Colors.BLUE_400)
        self.run_infos = ft.Column([ft.Row([self.category_icon,self.running_module]),self.info_text])
        self.left_run_menu = ft.Column([
            self.run_infos,ft.Row([ft.Container(self.progress_bar_module),self.progress_bar_module_text],width=260),
        ],alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        self.run_menu = ft.Container(ft.Container(ft.Row(
            [
                ft.Container(self.left_run_menu,padding=10),ft.VerticalDivider(), ft.Column([ft.Row([ft.Container(self.progress_and_start,padding=10)],alignment=ft.MainAxisAlignment.CENTER)],alignment=ft.MainAxisAlignment.CENTER),
            ], spacing=2
        ), bgcolor=MENU_COLOR, expand=True, padding=10
        ), bgcolor=ft.Colors.TRANSPARENT, border_radius=ft.border_radius.all(10),width=0,height=150,
            bottom=20, left=self.tools.left + self.tools.width + 5,blur=10,opacity=0,
            animate_opacity=ft.Animation(duration=300, curve=ft.AnimationCurve.LINEAR_TO_EASE_OUT),
            animate=ft.Animation(duration=300, curve=ft.AnimationCurve.LINEAR_TO_EASE_OUT),
            )

        self.scroll_horizontal_row = None
        self.work_area = None
        self.setup()
        self.pipeline_gui.build_show_room(self.page_stack)


        self.page_forward = ft.IconButton(icon=ft.Icons.CHEVRON_RIGHT_SHARP, on_click=lambda e: self.press_page_up(),
                                          icon_color=ft.Colors.WHITE60,
                                          style=ft.ButtonStyle(
                                         shape=ft.RoundedRectangleBorder(radius=12), ),
                                          visible=True if self.pipeline_gui.show_room_max_page_number != 1 else False,
                                          tooltip="Get to the next page", hover_color=ft.Colors.WHITE12)
        self.page_backward = ft.IconButton(icon=ft.Icons.CHEVRON_LEFT_SHARP, on_click=lambda e: self.press_page_down(),
                                           icon_color=ft.Colors.WHITE24,
                                           style=ft.ButtonStyle(
                                           shape=ft.RoundedRectangleBorder(radius=12), ), disabled=True,
                                           tooltip="Return to the last page", hover_color=ft.Colors.WHITE12, visible=True if self.pipeline_gui.show_room_max_page_number != 1 else False)

        self.switch_pages = ft.Container(ft.Container(ft.Row(
                    [
                        self.page_backward, self.page_forward,
                    ], tight=True,spacing=2
                ), bgcolor=MENU_COLOR, expand=True, height=40
                ), bgcolor=ft.Colors.TRANSPARENT, border_radius=ft.border_radius.all(10),
                    top=self.pipeline_gui.show_room_container.top + self.pipeline_gui.show_room_container.height + 5,
                    left=self.pipeline_gui.show_room_container.left,blur=10)
        self.page_stack.controls.append(self.switch_pages)
        self.page_stack.update()
        self.add_all_listeners()

    def run(self,ignore_check=False):
        show_room_names = [m.name for m in self.pipeline_gui.show_room_modules]
        if not ignore_check and not self.pipeline_gui.pipeline.check_pipeline_runnable(show_room_names):
            def dismiss_dialog(e):
                cupertino_alert_dialog.open = False
                e.control.page.update()
                for mod in self.pipeline_gui.modules.values():
                    if not self.pipeline_gui.pipeline.check_module_satisfied(mod.name):
                        if not mod.show_ports:
                            mod.ports_in_out_clicked()
            def dismiss_dialog_ignore(e):
                cupertino_alert_dialog.open = False
                e.control.page.update()
                self.run(True)
            cupertino_alert_dialog = ft.CupertinoAlertDialog(
                title=ft.Text("Mandatory Input Warning"),
                content=ft.Text("Not all mandatory inputs are satisfied."),
                actions=[
                    ft.CupertinoDialogAction(
                        "Change modules",is_default_action=True, on_click=dismiss_dialog
                    ),
                    ft.CupertinoDialogAction(text="Skip modules", is_destructive_action=True, on_click=dismiss_dialog_ignore),
                ],
            )
            self.page.overlay.append(cupertino_alert_dialog)
            cupertino_alert_dialog.open = True
            self.page.update()
            return
        self.info_text.spans = []
        self.info_text.value = "Idle, waiting for start."
        self.info_text.update()
        self.start_button.disabled = True
        self.start_button.update()
        for module in self.pipeline_gui.modules.values():
            self.pipeline_gui.lines_gui.update_delete_buttons(module,True)
            module.waiting_button.visible = True
            module.start_button.visible = False
            module.delete_button.visible = False
            module.waiting_button.update()
            module.start_button.update()
            module.delete_button.update()
            module.disable_tools()
        self.pipeline_gui.pipeline.run(show_room_names)
        self.pipeline_gui.modules_executed = 0
        self.update_modules_executed()
        self.start_button.disabled = False
        self.start_button.update()

    def add_all_listeners(self):
        pipeline_change_listener = PipelineChangeListener(self)
        self.pipeline_gui.pipeline.event_manager.subscribe(listener=pipeline_change_listener)
        module_executed_listener =ModuleExecutedListener(self)
        self.pipeline_gui.pipeline.event_manager.subscribe(listener=module_executed_listener)
        module_started_listener =ModuleStartedListener(self)
        self.pipeline_gui.pipeline.event_manager.subscribe(listener=module_started_listener)
        module_progress_listener =ModuleProgressListener(self)
        self.pipeline_gui.pipeline.event_manager.subscribe(listener=module_progress_listener)
        module_error_listener =ModuleErrorListener(self)
        self.pipeline_gui.pipeline.event_manager.subscribe(listener=module_error_listener)

    def update_modules_executed(self):
        current =self.pipeline_gui.modules_executed
        if not self.pipeline_gui.pipeline.running:
            total = len(self.pipeline_gui.pipeline.modules) - len(ModuleType) * 2
            self.progress_pipeline.value = (current / total) if total > 0 else 0
            self.pipeline_gui.module_running_count = total
            self.progress_text.value = f"{current}/{total}"
        else:
            self.progress_pipeline.value = (current / self.pipeline_gui.module_running_count) if self.pipeline_gui.module_running_count > 0 else 0
            self.progress_text.value = f"{current}/{self.pipeline_gui.module_running_count}"
        self.progress_text.update()
        self.page.update()

    def on_change(self,e,reference):
        """
        Handles if the name to save gets changed.
        """
        try:
            self.pipeline_gui.name = str(e.control.value)
            reference.current.color = ft.Colors.WHITE60
            self.pipeline_gui.page.update()
        except ValueError:
            self.pipeline_gui.page.snack_bar = ft.SnackBar(ft.Text(f"Pipeline name only allows str's."))
            self.pipeline_gui.page.snack_bar.open = True
            reference.current.value = self.name
            reference.current.color = ft.Colors.RED
            self.pipeline_gui.page.update()

    def on_select_file(self, e):
        """
        Handles if a file is selected.
        """
        if e.files is not None:
            #TODO: LOAD FILE with path
            pass

    def on_select_dir(self,e,text):
        """
        Handles if a directory is selected.
        """
        if e.path is not None:
            self.pipeline_gui.save_dir = e.path
            text.value = format_directory_path(e.path,20)
            text.update()
            self.page.update()

    def press_page_up(self):
        self.pipeline_gui.change_page(self.pipeline_gui.show_room_page_number+1)
        if self.pipeline_gui.show_room_page_number > 0:
            self.page_backward.icon_color = ft.Colors.WHITE60
            self.page_backward.disabled = False
            self.page_backward.update()
        if self.pipeline_gui.show_room_page_number >= self.pipeline_gui.show_room_max_page_number-1:
            self.page_forward.icon_color = ft.Colors.WHITE24
            self.page_forward.disabled = True
            self.page_forward.update()

    def press_page_down(self):
        self.pipeline_gui.change_page(self.pipeline_gui.show_room_page_number-1)
        if self.pipeline_gui.show_room_page_number == 0:
            self.page_backward.icon_color = ft.Colors.WHITE24
            self.page_backward.disabled = True
            self.page_backward.update()
        if self.pipeline_gui.show_room_page_number < self.pipeline_gui.show_room_max_page_number-1:
            self.page_forward.icon_color = ft.Colors.WHITE60
            self.page_forward.disabled = False
            self.page_forward.update()

    def scroll_horizontal(self,e):
        self.scroll_horizontal_row.scroll_to((self.work_area.width-self.page.window.width)*e.control.value, duration=1000)
        self.scroll_horizontal_row.update()

    def save_button_click(self,from_code=False):
        if self.save_menu.opacity==1:
            self.save_menu_button.icon_color = WHITE60
            self.save_menu_button.tooltip = f"Show save menu"
            self.save_menu_button.update()
            self.save_menu.width = 0
            self.save_menu.opacity = 0
            self.save_menu.update()
        else:
            self.save_menu_button.icon_color = ft.Colors.BLUE_400
            self.save_menu_button.tooltip = f"Hide save menu"
            self.save_menu_button.update()
            if not from_code and self.run_menu.opacity==1:
                self.run_menu_click(True)
            self.save_menu.width = 320
            self.save_menu.opacity = 1
            self.save_menu.update()

    def run_menu_click(self,from_code=False):
        if self.run_menu.opacity==1:
            self.run_menu_button.icon_color = WHITE60
            self.run_menu_button.tooltip = f"Show run menu"
            self.run_menu_button.update()
            self.run_menu.width = 0
            self.run_menu.opacity = 0
            self.run_menu.update()
        else:
            self.run_menu_button.icon_color = ft.Colors.BLUE_400
            self.run_menu_button.tooltip = f"Hide run menu"
            self.run_menu_button.update()
            if not from_code and self.save_menu.opacity==1:
                self.save_button_click(True)
            self.run_menu.width = 420
            self.run_menu.opacity = 1
            self.run_menu.update()

    def delete_button_click(self):
        #for module in self.pipeline_gui.modules.values():
        #    print(module.name,module.left,module.top)
        if self.pipeline_gui.show_delete_button:
            self.delete_button.icon_color = WHITE60
            self.delete_button.tooltip = f"Show delete buttons"
            self.pipeline_gui.show_delete_button = False
            self.pipeline_gui.lines_gui.update_all()
        else:
            self.delete_button.icon_color = ft.Colors.BLUE_400
            self.delete_button.tooltip = f"Hide delete buttons"
            self.pipeline_gui.show_delete_button = True
            if self.pipeline_gui.show_ports:
                self.port_button_click()
            self.pipeline_gui.lines_gui.update_all()

        self.delete_button.update()

    def port_button_click(self):
        if self.pipeline_gui.show_ports:
            self.port_button.icon_color = WHITE60
            self.port_button.tooltip = f"Show which ports get transferred"
            self.pipeline_gui.show_ports = False
            self.pipeline_gui.lines_gui.update_all()
        else:
            self.port_button.icon_color = ft.Colors.BLUE_400
            self.port_button.tooltip = f"Hide which ports get transferred"
            self.pipeline_gui.show_ports = True
            if self.pipeline_gui.show_delete_button:
                self.delete_button_click()
            self.pipeline_gui.lines_gui.update_all()

        self.port_button.update()


    def setup(self):
        self.work_area = ft.Container(
            content=self.pipeline_gui,
            width=10000,
            height=10000,
            bgcolor=ft.Colors.TRANSPARENT,
        )
        self.scroll_horizontal_row = ft.Row(
            [self.work_area], scroll=ft.ScrollMode.ALWAYS)

        def on_vertical_scroll(e:ft.OnScrollEvent):
            self.pipeline_gui.offset_y = e.pixels

        scroll_area = ft.Container(
            content=ft.Column([self.scroll_horizontal_row], scroll=ft.ScrollMode.ALWAYS,on_scroll=on_vertical_scroll),
            height=self.page.window.height,
            width=self.page.window.width,
            expand=True,
        )


        def on_resize(e: ft.WindowResizeEvent):
            scroll_area.height = e.height
            scroll_area.width = e.width
            self.pipeline_gui.update_show_room()
            scroll_area.update()

        self.page.on_resized = on_resize

        self.page_stack = ft.Stack([
                scroll_area,
                self.tools,
                self.save_menu,
                self.run_menu,
             ]
            )

        self.page.add(
            self.page_stack,
        )

def main(page: ft.Page):
    builder = Builder(page)
    pipeline_gui = builder.pipeline_gui
    module_gui1 = pipeline_gui.add_module(ModuleType.READ_LIF,891.0,262.0)
    module_gui2 = pipeline_gui.add_module(ModuleType.BATCH_IMAGE_SEG,460.0,259.0)
    module_gui3 = pipeline_gui.add_module(ModuleType.BATCH_IMAGE_READOUT,466.0,33.0)
    module_gui4 = pipeline_gui.add_module(ModuleType.BATCH_IMAGE_READOUT,751.0,30.0)
    pipeline_gui.add_connection(module_gui1,module_gui2,["image_paths","mask_paths"])
    pipeline_gui.add_connection(module_gui2,module_gui3,["mask_paths"])
    pipeline_gui.add_connection(module_gui2, module_gui4, ["mask_paths"])
    pipeline_gui.add_connection(module_gui1, module_gui4, ["image_paths"])

ft.app(main)
