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
        self.port_selection = False
        self.module = self.pipeline_gui.pipeline.add_module(module_type.value)
        self.pipeline_gui.modules[self.module.module_id] = self
        self.color = self.module.gui_config().category.value
        self.valid = False
        self.click_container = ft.Container(on_click=lambda e: self.add_connection(), height=MODULE_HEIGHT, width=MODULE_WIDTH,
                                            visible=False,bgcolor=ft.Colors.BLACK12,disabled=True,border_radius=ft.border_radius.all(10))
        self.click_gesture = ft.GestureDetector(visible=False,disabled=True,content=self.click_container,on_enter=lambda e: self.on_enter_click_module(),on_exit=lambda e: self.on_exit_click_module())
        self.connect = ft.IconButton(icon=ft.Icons.SHARE, icon_color=ft.Colors.WHITE60,
                                                      style=ft.ButtonStyle(
                                                          shape=ft.RoundedRectangleBorder(radius=12),
                                                      ), on_click=lambda e: self.connect_clicked(),
                                                      tooltip="Add connection",hover_color=ft.Colors.WHITE12,visible=self.module.outputs!={})
        self.options = ft.IconButton(icon=ft.Icons.TUNE, icon_color=ft.Colors.WHITE54,
                                                      style=ft.ButtonStyle(
                                                          shape=ft.RoundedRectangleBorder(radius=12),
                                                      ), on_click=lambda e: self.add_connection(),
                                                      tooltip="Options",hover_color=ft.Colors.WHITE12,)
        self.tools = ft.Container(ft.Row(
                                            [
                                                self.connect,self.options,
                                            ],tight=True
                                        ),bgcolor=ft.Colors.BLACK12,expand=True,width=MODULE_WIDTH,
                                        )

        self.delete_button = ft.IconButton(ft.icons.CLOSE,icon_color=ft.Colors.WHITE,hover_color=ft.Colors.WHITE12,tooltip="Delete Module",on_click=lambda e:self.remove_module())
        self.port_chips = self.get_ports_row()
        self.connection_ports = ft.Container(
            self.port_chips,visible=False
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
        self.content = ft.Column([ft.Stack([
                self.module_container,
                ft.Container(content=self.delete_button,margin=ft.margin.only(top=-7, left=7),alignment=ft.alignment.top_right,width=MODULE_WIDTH,
                             ),
                self.click_gesture
        ]
        )
            ,self.connection_ports
        ],tight=True
        )

    def on_enter_click_module(self):
        if self.valid:
            self.click_container.bgcolor = ft.Colors.WHITE24
            self.click_container.update()

    def on_exit_click_module(self):
        if self.valid:
            self.click_container.bgcolor = ft.Colors.TRANSPARENT
            self.click_container.update()


    def connect_clicked(self):
        self.pipeline_gui.toggle_all_module_detection(self.name)
        if not self.port_selection:
            self.connection_ports.visible = True
            self.connection_ports.update()
            self.connect.icon_color = ft.Colors.BLACK38
            self.connect.update()
            self.delete_button.visible = False
            self.delete_button.update()
            self.port_selection = True
        else:
            self.valid = False
            self.connection_ports.visible = False
            self.port_chips = self.get_ports_row()
            self.connection_ports.content = self.port_chips
            self.connection_ports.update()
            self.connect.icon_color = ft.Colors.WHITE60
            self.connect.update()
            self.delete_button.visible = True
            self.delete_button.update()
            self.port_selection = False


    def set_valid(self):
        self.valid = True
        self.click_container.bgcolor = ft.Colors.TRANSPARENT
        self.module_container.border = ft.border.all(2, ft.Colors.WHITE38)
        self.module_container.update()
        self.click_container.update()

    def set_invalid(self):
        self.valid = False
        self.click_container.bgcolor = ft.Colors.BLACK12
        self.module_container.border = ft.border.all(2, ft.Colors.BLACK12)
        self.module_container.update()
        self.click_container.update()

    def get_ports_row(self):
        ports_chips = ft.Row()

        for port_name in self.module.outputs.keys():
            ports_chips.controls.append(
                ft.Chip(
                    label=ft.Text(port_name),
                    on_select=lambda e: self.select_port(e,port_name),
                )
            )
        return ports_chips

    def select_port(self,e, port_name):
        if e.control.selected:
            self.pipeline_gui.transmitting_ports.append(port_name)
            self.port_chips.update()
        else:
            self.pipeline_gui.transmitting_ports.remove(port_name)
            self.port_chips.update()

        self.pipeline_gui.check_for_valid()

    def toggle_detection(self):
        if self.detection:
            self.detection = False
            self.click_container.disabled = False
            self.click_container.visible = True
            self.click_container.update()
            self.click_gesture.disabled = False
            self.click_gesture.visible = True
            self.click_gesture.update()
            self.delete_button.visible = False
            self.delete_button.update()
        else:
            self.detection = True
            self.set_invalid()
            self.click_container.disabled = True
            self.click_container.bg_color = ft.Colors.BLACK12
            self.click_container.visible = False
            self.click_container.update()
            self.click_gesture.disabled = True
            self.click_gesture.visible = False
            self.click_gesture.update()
            self.delete_button.visible = True
            self.delete_button.update()
            self.connection_ports.visible = False
            self.connect.update()



    def add_connection(self):
        if self.pipeline_gui.source_module is not None and self.pipeline_gui.transmitting_ports is not None and not self.detection and self.valid:
            self.pipeline_gui.add_connection(self.pipeline_gui.modules[self.pipeline_gui.source_module],self,self.pipeline_gui.transmitting_ports)
            self.pipeline_gui.check_for_valid()

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
