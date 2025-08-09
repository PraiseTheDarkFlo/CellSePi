import flet as ft
from click import style
from jeepney.low_level import padding

from cellsepi.expert_constants import *


class ModuleGUI(ft.GestureDetector):
    def __init__(self, pipeline_gui,module_type: ModuleType):
        super().__init__()
        self.pipeline_gui = pipeline_gui
        self.detection: bool = True
        self.module_type = module_type
        self.mouse_cursor = ft.MouseCursor.MOVE
        self.drag_interval = 5
        self.on_pan_start = self.start_drag
        self.on_pan_update = self.drag
        self.on_pan_end = self.drop
        self.left = BUILDER_WIDTH/2
        self.top = BUILDER_HEIGHT/2
        self.old_left = None
        self.old_top = None
        self.module = self.pipeline_gui.pipeline.add_module(module_type.value)
        self.pipeline_gui.modules[self.module.module_id] = self
        self.color = self.module.gui_config().category.value
        self.click_container = ft.Container(on_click=lambda e: self.add_connection(), height=MODULE_HEIGHT, width=MODULE_WIDTH,
                                            visible=False,bgcolor=None,disabled=True)
        self.on_enter = lambda e: self.on_enter_module()
        self.on_exit = lambda e: self.on_leave_module()
        self.connect = ft.IconButton(icon=ft.Icons.SHARE, icon_color=ft.Colors.WHITE60,
                                                      style=ft.ButtonStyle(
                                                          shape=ft.RoundedRectangleBorder(radius=12),
                                                      ), on_click=lambda e: self.pipeline_gui.connect(self.name),
                                                      tooltip="Add connection",hover_color=ft.Colors.WHITE12)
        self.options = ft.IconButton(icon=ft.Icons.TUNE, icon_color=ft.Colors.WHITE54,
                                                      style=ft.ButtonStyle(
                                                          shape=ft.RoundedRectangleBorder(radius=12),
                                                      ), on_click=lambda e: self.on_enter_module(),
                                                      tooltip="Options",hover_color=ft.Colors.WHITE12,)
        self.tools = ft.Container(ft.Row(
                                            [
                                                self.connect,self.options,
                                            ],tight=True
                                        ),bgcolor=ft.Colors.BLACK12,expand=True,width=MODULE_WIDTH,
                                        )
        self.module_container = ft.Container(
                    content=ft.Column(
                                [
                                        ft.Container(ft.Row(
                                                [
                                                ft.Text(value=self.module.gui_config().name,
                                                    weight=ft.FontWeight.BOLD,
                                                    width=MODULE_WIDTH-40,
                                                    height=20,color=ft.Colors.BLACK),
                                               ]
                                              ),padding=ft.padding.only(left=5, top=5)),
                                            self.tools,
                                       ],
                                    tight=True)
                    ,bgcolor=self.color,width=MODULE_WIDTH
                    ,height=MODULE_HEIGHT,
                    border=ft.border.all(2, ft.Colors.BLACK12),
                    border_radius=ft.border_radius.all(10)
                )
        self.content = ft.Stack([
                self.module_container,
                ft.Container(content=ft.IconButton(ft.icons.CLOSE,icon_color=ft.Colors.WHITE,hover_color=ft.Colors.WHITE12,tooltip="Delete Module",on_click=lambda e:self.remove_module()),margin=ft.margin.only(top=-7, left=7),alignment=ft.alignment.top_right,width=MODULE_WIDTH,
                             ),
                self.click_container
        ]
        )

    def on_enter_module(self):
        if not self.detection:
            self.click_container.bg_color = ft.Colors.BLACK12
            self.module_container.border_color = ft.Colors.ORANGE_700

    def on_leave_module(self):
        if not self.detection:
            self.click_container.bg_color = None
            self.module_container.border_color = ft.Colors.ORANGE_700

    def toggle_detection(self):
        if self.detection:
            self.detection = False
            self.mouse_cursor = ft.MouseCursor.CLICK
            self.click_container.disabled = False
            self.click_container.visible = True
        else:
            self.detection = True
            self.mouse_cursor = ft.MouseCursor.MOVE
            self.click_container.disabled = True
            self.click_container.visible = False

    def add_connection(self):
        if self.pipeline_gui.source_module is not None and self.pipeline_gui.transmitting_ports is not None and not self.detection:
            self.pipeline_gui.pipeline.add_connection(self.pipeline_gui.source_module,self,self.pipeline_gui.transmitting_ports)


    def remove_module(self):
        for pipe in list(self.pipeline_gui.pipeline.pipes_in[self.name]):
            self.pipeline_gui.remove_connection(self.pipeline_gui.modules[pipe.source_module.module_id],self)
        for pipe in list(self.pipeline_gui.pipeline.pipes_out[self.name]):
            self.pipeline_gui.remove_connection(self,self.pipeline_gui.modules[pipe.target_module.module_id])

        self.pipeline_gui.remove_module(self.name)


    @property
    def name(self):
        return self.module.module_id

    def bounce_back(self):
        """Returns card to its original position"""
        self.left = self.old_left
        self.top = self.old_top
        self.update()

    def start_drag(self, e: ft.DragStartEvent):
        if self.detection:
            self.old_left = self.left
            self.old_top = self.top
            self.pipeline_gui.lines_gui.update_lines(self)
            self.update()

    def drag(self, e: ft.DragUpdateEvent):
        if self.detection:
            self.top = max(0, self.top + e.delta_y)
            self.left = max(0, self.left + e.delta_x)
            self.pipeline_gui.lines_gui.update_lines(self)
            self.update()

    def drop(self,e: ft.DragEndEvent):
        if self.detection:
            for module in self.pipeline_gui.modules.values():
                if module is self:
                    continue

                overlap = not (
                        self.left + MODULE_WIDTH < module.left or
                        self.left > module.left + MODULE_WIDTH or
                        self.top + MODULE_HEIGHT < module.top or
                        self.top > module.top + MODULE_HEIGHT
                )

                if overlap:
                    self.bounce_back()
                    self.pipeline_gui.lines_gui.update_lines(self)
                    e.control.update()
                    return

            e.control.update()
            self.pipeline_gui.lines_gui.update_lines(self)
