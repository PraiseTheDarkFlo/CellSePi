
import flet as ft
from flet_core.cupertino_colors import WHITE
from sympy.printing.tree import print_node

from cellsepi.expert_constants import *


class ModuleGUI(ft.GestureDetector):
    def __init__(self, pipeline_gui,module_type: ModuleType,x: float = None,y: float = None):
        super().__init__()
        self.pipeline_gui = pipeline_gui
        self.detection: bool = True
        self.module_type = module_type
        self.mouse_cursor = ft.MouseCursor.MOVE
        self.drag_interval = 5
        self.on_pan_start = self.start_drag
        self.on_pan_update = self.drag
        self.on_pan_end = self.drop
        self.left = BUILDER_WIDTH/2 if x is None else x
        self.top = BUILDER_HEIGHT/2 if y is None else y
        self.old_left = None
        self.old_top = None
        self.port_selection = False
        self.module = self.pipeline_gui.pipeline.add_module(module_type.value)
        self.pipeline_gui.modules[self.module.module_id] = self
        self.color = self.module.gui_config().category.value
        self.valid = False
        self.click_container = ft.Container(on_click=lambda e: self.add_connection(), height=MODULE_HEIGHT, width=MODULE_WIDTH,
                                            visible=False,bgcolor=INVALID_COLOR,disabled=True,border_radius=ft.border_radius.all(10))
        self.click_gesture = ft.GestureDetector(visible=False,disabled=True,content=self.click_container,on_enter=lambda e: self.on_enter_click_module(),on_exit=lambda e: self.on_exit_click_module())
        self.connect_button = ft.IconButton(icon=ft.Icons.SHARE, icon_color=ft.Colors.WHITE60,
                                            style=ft.ButtonStyle(
                                                          shape=ft.RoundedRectangleBorder(radius=12),
                                                      ), on_click=lambda e: self.connect_clicked(),
                                            tooltip="Add connection", hover_color=ft.Colors.WHITE12, visible=self.module.outputs!={})

        self.options_button = ft.IconButton(icon=ft.Icons.TUNE, icon_color=ft.Colors.WHITE54,
                                            style=ft.ButtonStyle(
                                                          shape=ft.RoundedRectangleBorder(radius=12),
                                                      ), on_click=lambda e: self.add_connection(),
                                            tooltip="Options", hover_color=ft.Colors.WHITE12, )

        self.show_ports = False
        self.ports_in_out_button = ft.IconButton(icon=ft.Icons.SYNC_ALT_ROUNDED, icon_color=ft.Colors.WHITE60,
                                                 style=ft.ButtonStyle(
                                              shape=ft.RoundedRectangleBorder(radius=12),
                                          ), on_click=lambda e: self.ports_in_out_clicked(),
                                                 tooltip="View Ports", hover_color=ft.Colors.WHITE12)

        self.tools = ft.Container(ft.Row(
                                            [
                                                self.connect_button,self.options_button,self.ports_in_out_button
                                            ],tight=True
                                        ),bgcolor=ft.Colors.BLACK12,expand=True,width=MODULE_WIDTH,
                                        )

        self.delete_button = ft.IconButton(ft.icons.CLOSE,icon_color=ft.Colors.WHITE,hover_color=ft.Colors.WHITE12,tooltip="Delete Module",on_click=lambda e:self.remove_module())
        self.port_chips = self.get_ports_row()
        self.connection_ports = ft.Container(
            self.port_chips,visible=False
        )

        control_list_ports = []
        self.in_ports_icons = {}
        self.in_ports_icons_occupied = {}
        for port in self.module.inputs.values():
            if not port.opt:
                self.in_ports_icons[port.name] = ft.Stack([ft.Container(bgcolor=ft.Colors.RED,width=30,height=30,border_radius=ft.border_radius.all(45)),ft.IconButton(ft.Icons.CLOSE,disabled=True,hover_color=ft.Colors.TRANSPARENT,icon_color=WHITE,tooltip=f"Port '{port.name}' is mandatory and has no incoming pipe!")],alignment=ft.alignment.center,visible=not self.pipeline_gui.pipeline.check_ports_occupied(self.name,[port.name]))
                self.in_ports_icons_occupied[port.name] = ft.Stack([ft.Container(bgcolor=ft.Colors.GREEN,width=30,height=30,border_radius=ft.border_radius.all(45)),ft.IconButton(ft.Icons.CHECK,disabled=True,hover_color=ft.Colors.TRANSPARENT,icon_color=WHITE,tooltip=f"Port '{port.name}' is mandatory and is satisfied.")],alignment=ft.alignment.center,visible= self.pipeline_gui.pipeline.check_ports_occupied(self.name,[port.name]))
            else:
                self.in_ports_icons[port.name] = ft.Stack([ft.Container(bgcolor=ft.Colors.RED,width=30,height=30,border_radius=ft.border_radius.all(45)),ft.IconButton(ft.Icons.CLOSE,disabled=True,hover_color=ft.Colors.TRANSPARENT,icon_color=WHITE,tooltip=f"Port '{port.name}' is optional and has no incoming pipe.")],alignment=ft.alignment.center,opacity=0.2,visible=not self.pipeline_gui.pipeline.check_ports_occupied(self.name,[port.name]))
                self.in_ports_icons_occupied[port.name] = ft.Stack([ft.Container(bgcolor=ft.Colors.GREEN,width=30,height=30,border_radius=ft.border_radius.all(45)),ft.IconButton(ft.Icons.CHECK,disabled=True,hover_color=ft.Colors.TRANSPARENT,icon_color=WHITE,tooltip=f"Port '{port.name}' is optional and is satisfied.")],alignment=ft.alignment.center,opacity=0.2,visible= self.pipeline_gui.pipeline.check_ports_occupied(self.name,[port.name]))

        in_ports = ft.Column([ft.Row([ft.Text(port.name,width=MODULE_WIDTH/2,weight=ft.FontWeight.BOLD,color=ft.Colors.WHITE),self.in_ports_icons[port.name],self.in_ports_icons_occupied[port.name]]) for port in self.module.inputs.values()],spacing=0)
        out_ports = ft.Column([ft.Row([ft.Text(port.name,width=MODULE_WIDTH/2,weight=ft.FontWeight.BOLD,color=ft.Colors.WHITE)]) for port in self.module.outputs.values()])
        input_text=ft.Text("Inputs:",size=20,weight=ft.FontWeight.BOLD,color=ft.Colors.WHITE)
        output_text=ft.Text("Outputs:",size=20,weight=ft.FontWeight.BOLD,color=ft.Colors.WHITE)
        if self.module.inputs != {}:
            control_list_ports.append(input_text)
            control_list_ports.append(in_ports)
        if self.module.outputs != {}:
            control_list_ports.append(output_text)
            control_list_ports.append(out_ports)

        self.warning_satisfied = ft.Stack([ft.Container(bgcolor=WHITE,width=10,height=20,bottom=2,right=9,border_radius=ft.border_radius.all(45)),ft.IconButton(ft.Icons.WARNING_ROUNDED,icon_size=35,disabled=True,hover_color=ft.Colors.TRANSPARENT,icon_color=ft.Colors.RED,tooltip=f"Not all mandatory inputs are satisfied!")],alignment=ft.alignment.center,visible=not self.pipeline_gui.pipeline.check_module_satisfied(self.name),width=40,height=40,top=-5,left=MODULE_WIDTH-65)
        self.module_container = ft.Container(
                    content=ft.Column(
                                [
                                        ft.Container(ft.Row(
                                                [
                                                ft.Text(value=self.module.gui_config().name,
                                                    weight=ft.FontWeight.BOLD,
                                                    width=MODULE_WIDTH-60,
                                                    height=20,color=ft.Colors.BLACK),
                                               ],height=20
                                              ),padding=ft.padding.only(left=5, top=5)),
                                            self.tools,
                                       ],
                                    tight=True)
                    ,bgcolor=self.color,width=MODULE_WIDTH
                    ,height=MODULE_HEIGHT,
                    border=ft.border.all(4, ft.Colors.RED if not self.pipeline_gui.pipeline.check_module_satisfied(self.name) else ft.Colors.BLACK12),
                    border_radius=ft.border_radius.all(10)
                )
        self.ports_container = ft.Container(
            content=ft.Column(controls=control_list_ports, scroll=ft.ScrollMode.ALWAYS), bgcolor=self.color,
            width=MODULE_WIDTH,
            border_radius=ft.border_radius.all(10), padding=10, top=self.module_container.height-15,
            border=ft.border.all(8, ft.Colors.BLACK12), height=MODULE_HEIGHT * 2, visible=False
        )
        self.content = ft.Stack([
            self.ports_container,
            ft.Column([ft.Stack([
                self.module_container,
                ft.Container(content=self.delete_button,margin=ft.margin.only(top=-7, left=7),alignment=ft.alignment.top_right,width=MODULE_WIDTH,
                             ),
                self.warning_satisfied,
                self.click_gesture
        ]
        ),
        self.connection_ports

        ],tight=True
        )],height=self.module_container.height,
        )

    def on_enter_click_module(self):
        if self.valid:
            self.click_container.bgcolor = VALID_COLOR
            self.click_container.update()

    def on_exit_click_module(self):
        if self.valid:
            self.click_container.bgcolor = ft.Colors.TRANSPARENT
            self.click_container.update()

    def update_port_icons(self):
        for port in self.module.inputs.keys():
            if self.pipeline_gui.pipeline.check_ports_occupied(self.name, [port]):
                self.in_ports_icons[port].visible = False
                self.in_ports_icons_occupied[port].visible = True
            else:
                self.in_ports_icons[port].visible = True
                self.in_ports_icons_occupied[port].visible = False

            self.in_ports_icons[port].update()
            self.in_ports_icons_occupied[port].update()

            self.module_container.border = ft.border.all(4, ft.Colors.RED if not self.pipeline_gui.pipeline.check_module_satisfied(self.name) else ft.Colors.BLACK12)
            self.module_container.update()
            self.warning_satisfied.visible = not self.pipeline_gui.pipeline.check_module_satisfied(self.name)
            self.warning_satisfied.update()

    def connect_clicked(self,update:bool=True):
        self.pipeline_gui.toggle_all_module_detection(self.name)
        if not self.port_selection:
            if self.show_ports:
                self.ports_in_out_clicked(False)
            if update:
                self.pipeline_gui.set_in_background(self,True)
            self.connection_ports.visible = True
            self.connect_button.icon_color = ft.Colors.BLACK38
            self.delete_button.visible = False
            self.content.height = 40+self.module_container.height
            self.port_selection = True
        else:
            self.valid = False
            self.connection_ports.visible = False
            self.port_chips = self.get_ports_row()
            self.connection_ports.content = self.port_chips
            self.connect_button.icon_color = ft.Colors.WHITE60
            self.delete_button.visible = True
            self.content.height = self.module_container.height
            self.port_selection = False

        self.connection_ports.update()
        self.connect_button.update()
        self.delete_button.update()
        self.content.update()

    def ports_in_out_clicked(self,update:bool=True):
        if not self.show_ports:
            if self.port_selection:
                self.connect_clicked(False)
            if update:
                self.pipeline_gui.set_in_foreground(self)
            self.ports_container.visible = True
            self.content.height = self.ports_container.height + self.module_container.height - 15
            self.ports_in_out_button.icon_color = ft.Colors.BLACK38
            self.show_ports = True
        else:
            self.ports_container.visible = False
            self.ports_in_out_button.icon_color = ft.Colors.WHITE38
            self.content.height = self.module_container.height
            self.show_ports = False

        self.ports_container.update()
        self.content.update()
        self.ports_in_out_button.update()
        self.update()


    def set_valid(self):
        self.valid = True
        self.click_container.bgcolor = ft.Colors.TRANSPARENT
        self.module_container.border = ft.border.all(4, ft.Colors.WHITE38)
        self.module_container.update()
        self.click_container.update()

    def set_invalid(self):
        self.valid = False
        self.click_container.bgcolor = INVALID_COLOR
        self.module_container.border = ft.border.all(4, ft.Colors.RED if not self.pipeline_gui.pipeline.check_module_satisfied(self.name) else ft.Colors.BLACK12)
        self.module_container.update()
        self.click_container.update()

    def get_ports_row(self):
        ports_chips = ft.Row()

        for port_name in self.module.outputs.keys():
            ports_chips.controls.append(
                ft.Chip(
                    label=ft.Text(port_name),
                    on_select=lambda e,name = port_name: self.select_port(e,name),
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
            self.connect_button.update()


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
        self.old_left = self.left
        self.old_top = self.top
        self.pipeline_gui.lines_gui.update_lines(self)
        self.update()

    def drag(self, e: ft.DragUpdateEvent):
        self.top = max(0, self.top + e.delta_y)
        self.left = max(0, self.left + e.delta_x)
        self.pipeline_gui.lines_gui.update_lines(self)
        self.update()

    def drop(self,e: ft.DragEndEvent):
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
