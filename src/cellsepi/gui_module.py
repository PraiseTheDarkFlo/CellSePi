
import flet as ft
from flet_core.cupertino_colors import WHITE

from cellsepi.backend.main_window.expert_mode.module import FilePath, DirectoryPath
from cellsepi.expert_constants import *
from cellsepi.frontend.main_window.gui_directory import format_directory_path


class ModuleGUI(ft.GestureDetector):
    """
    Manages the GUI parts of the module.
    """
    def __init__(self, pipeline_gui,module_type: ModuleType,x: float = None,y: float = None,show_mode:bool=False):
        super().__init__()
        self.pipeline_gui = pipeline_gui
        self.detection: bool = True
        self.module_type = module_type
        self.mouse_cursor = ft.MouseCursor.MOVE
        self.show_mode = show_mode
        self.drag_interval = 5
        self.on_pan_start = self.start_drag
        self.on_pan_update = self.drag
        self.on_pan_end = self.drop
        self.show_offset_y = y
        self.left = BUILDER_WIDTH/2 if x is None else x
        self.top = BUILDER_HEIGHT/2 if y is None else y
        self.old_left = None
        self.old_top = None
        self.port_selection = False
        self.module = self.pipeline_gui.pipeline.add_module(module_type.value)
        if self.module.settings is None and hasattr(self.module, "_settings"):
            self.module._settings = self.generate_options_overlay()
        if show_mode:
            self.pipeline_gui.show_room_modules.append(self)
        else:
            self.pipeline_gui.modules[self.module.module_id] = self
        self.color = self.module.gui_config().category.value
        self.valid = False
        self.click_container = ft.Container(on_click=lambda e: self.add_connection(), height=MODULE_HEIGHT, width=MODULE_WIDTH,
                                            visible=False if not show_mode else True,bgcolor=INVALID_COLOR if not show_mode else ft.Colors.TRANSPARENT,disabled=True if not show_mode else False,border_radius=ft.border_radius.all(10))
        self.click_gesture = ft.GestureDetector(visible=False if not show_mode else True,disabled=True if not show_mode else False,content=self.click_container,on_enter=lambda e: self.on_enter_click_module(),on_exit=lambda e: self.on_exit_click_module())
        self.connect_button = ft.IconButton(icon=ft.Icons.SHARE, icon_color=ft.Colors.WHITE60,
                                            style=ft.ButtonStyle(
                                                          shape=ft.RoundedRectangleBorder(radius=12),
                                                      ), on_click=lambda e: self.connect_clicked(),
                                            tooltip="Add connection", hover_color=ft.Colors.WHITE12, visible=self.module.outputs!={})

        self.options_button = ft.IconButton(icon=ft.Icons.TUNE, icon_color=ft.Colors.WHITE60,
                                            style=ft.ButtonStyle(
                                                          shape=ft.RoundedRectangleBorder(radius=12),
                                                      ), on_click=lambda e: self.open_options(e),
                                            tooltip="Options", hover_color=ft.Colors.WHITE12, visible=True if self.module.settings is not None else False,)
        self.copy_button = ft.IconButton(icon=ft.Icons.CONTENT_COPY, icon_color=ft.Colors.WHITE60,
                                            style=ft.ButtonStyle(
                                                          shape=ft.RoundedRectangleBorder(radius=12),
                                                      ), on_click=lambda e: self.copy_module(),
                                            tooltip="Copy module", hover_color=ft.Colors.WHITE12,)
        self.start_button = ft.IconButton(icon=ft.Icons.PLAY_ARROW, icon_color=ft.Colors.BLACK12,disabled=True,
                                         style=ft.ButtonStyle(
                                             shape=ft.RoundedRectangleBorder(radius=12),
                                         ), on_click=lambda e: self.copy_module(),
                                         tooltip="Start pipeline from here", hover_color=ft.Colors.WHITE12, )

        self.show_ports = False
        self.ports_in_out_button = ft.IconButton(icon=ft.Icons.SYNC_ALT_ROUNDED, icon_color=ft.Colors.WHITE60,
                                                 style=ft.ButtonStyle(
                                              shape=ft.RoundedRectangleBorder(radius=12),
                                          ), on_click=lambda e: self.ports_in_out_clicked(),
                                                 tooltip="View ports", hover_color=ft.Colors.WHITE12)

        self.tools = ft.Container(ft.Row(
                                            [
                                                self.connect_button,self.options_button,self.ports_in_out_button,self.copy_button,self.start_button,
                                            ],tight=True,spacing=7
                                        ),bgcolor=ft.Colors.BLACK12,expand=True,width=MODULE_WIDTH
                                        )

        self.delete_button = ft.IconButton(ft.icons.CLOSE,visible=True if not show_mode else False,icon_color=ft.Colors.WHITE,hover_color=ft.Colors.WHITE12,tooltip="Delete Module",on_click=lambda e:self.remove_module())
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

        self.warning_satisfied = ft.Stack([ft.Container(bgcolor=WHITE,width=10,height=20,bottom=2,right=9,border_radius=ft.border_radius.all(45)),ft.IconButton(ft.Icons.WARNING_ROUNDED,icon_size=35,disabled=True,hover_color=ft.Colors.TRANSPARENT,icon_color=ft.Colors.RED,tooltip=f"Not all mandatory inputs are satisfied!")],alignment=ft.alignment.center,visible=not self.pipeline_gui.pipeline.check_module_satisfied(self.name) and not show_mode,width=40,height=40,top=-5,left=MODULE_WIDTH-65)
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
                    border=ft.border.all(4, ft.Colors.RED if not self.pipeline_gui.pipeline.check_module_satisfied(self.name) and not show_mode else ft.Colors.BLACK12),
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
        """
        Handles if the mouse enters hovering over the module to connect.
        """
        if self.valid:
            self.click_container.bgcolor = VALID_COLOR
            self.click_container.update()

    def on_exit_click_module(self):
        """
        Handles if the mouse exits hovering over the module to connect.
        """
        if self.valid:
            self.click_container.bgcolor = ft.Colors.TRANSPARENT
            self.click_container.update()

    def update_port_icons(self):
        """
        Updates all ports_icons of the show ports tab.
        """
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
        """
        Handles the event when the connection button gets pressed.
        """
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
        """
        Handles the event when the show ports button gets pressed.
        """
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
            self.ports_in_out_button.icon_color = ft.Colors.WHITE60
            self.content.height = self.module_container.height
            self.show_ports = False

        self.ports_container.update()
        self.content.update()
        self.ports_in_out_button.update()
        self.update()


    def set_valid(self):
        """
        Sets a module valid to connect.
        """
        self.valid = True
        self.click_container.bgcolor = ft.Colors.TRANSPARENT
        self.module_container.border = ft.border.all(4, ft.Colors.WHITE38)
        self.module_container.update()
        self.click_container.update()

    def set_invalid(self):
        """
        Sets a module to invalid to connect.
        """
        self.valid = False
        self.click_container.bgcolor = INVALID_COLOR
        self.module_container.border = ft.border.all(4, ft.Colors.RED if not self.pipeline_gui.pipeline.check_module_satisfied(self.name) else ft.Colors.BLACK12)
        self.module_container.update()
        self.click_container.update()

    def get_ports_row(self):
        """
        Creates the chip row for the different ports of a module.
        """
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
        """
        Handles the event if a port gets selected for connecting.
        """
        if e.control.selected:
            self.pipeline_gui.transmitting_ports.append(port_name)
            self.port_chips.update()
        else:
            self.pipeline_gui.transmitting_ports.remove(port_name)
            self.port_chips.update()

        self.pipeline_gui.check_for_valid()

    def toggle_detection(self):
        """
        Toggles between the module state 'only moveable' and  'normal mode'
        """
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
        """
        Handles the last step of the adding event when the target gets selected.
        """
        if self.pipeline_gui.source_module is not None and self.pipeline_gui.transmitting_ports is not None and not self.detection and self.valid:
            self.pipeline_gui.add_connection(self.pipeline_gui.modules[self.pipeline_gui.source_module],self,self.pipeline_gui.transmitting_ports)
            self.pipeline_gui.check_for_valid()

    def remove_module(self):
        """
        Removes a module and all its connections.
        """
        for pipe in list(self.pipeline_gui.pipeline.pipes_in[self.name]):
            self.pipeline_gui.remove_connection(self.pipeline_gui.modules[pipe.source_module.module_id],self)
        for pipe in list(self.pipeline_gui.pipeline.pipes_out[self.name]):
            self.pipeline_gui.remove_connection(self,self.pipeline_gui.modules[pipe.target_module.module_id])

        self.pipeline_gui.remove_module(self.name)


    @property
    def name(self):
        """
        Returns the module id of the module.
        """
        return self.module.module_id

    def bounce_back(self):
        """Returns card to its original position"""
        self.left = self.old_left
        self.top = self.old_top
        self.update()

    def start_drag(self, e: ft.DragStartEvent):
        """
        Handles the start of the drag event to save old location to make it possible to bounce back.
        """
        self.old_left = self.left
        self.old_top = self.top
        self.pipeline_gui.lines_gui.update_lines(self)
        self.update()

    def drag(self, e: ft.DragUpdateEvent):
        """
        Handles the drag event.
        """
        self.top = max(0, self.top + e.delta_y)
        self.left = max(0, self.left + e.delta_x)
        self.pipeline_gui.lines_gui.update_lines(self)
        self.update()

    def drop(self,e: ft.DragEndEvent):
        """
        Handles the drop event.
        """
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

        overlap_show_room = not (
                self.left + MODULE_WIDTH  < self.pipeline_gui.show_room_container.left or
                self.left > self.pipeline_gui.show_room_container.left + self.pipeline_gui.show_room_container.width or
                self.top + MODULE_HEIGHT < self.pipeline_gui.show_room_container.top or
                self.top > self.pipeline_gui.show_room_container.top + self.pipeline_gui.show_room_container.height
        ) and self.show_mode

        if overlap_show_room:
            self.bounce_back()
            e.control.update()
            return
        elif self.show_mode:
            self.show_mode = False
            self.pipeline_gui.modules[self.name] = self
            self.pipeline_gui.show_room_modules.remove(self)
            self.pipeline_gui.refill_show_room(self)
            self.click_container.disabled = True
            self.click_container.bgcolor = INVALID_COLOR
            self.click_container.visible = False
            self.click_gesture.disabled = True
            self.click_gesture.visible = False
            self.delete_button.visible = True
            self.click_container.update()
            self.click_gesture.update()

        e.control.update()
        self.pipeline_gui.lines_gui.update_lines(self)

    def generate_options_overlay(self):
        """
        Generates with the user attributes tagged with the prefix 'user_' a gui overlay.
        """
        user_attributes = self.module.get_user_attributes

        height = 72* len(user_attributes) + 10 * (len(user_attributes)-1)+10 #72 because 60 only apples on the inner measurements
        calc_height = height>260
        if len(user_attributes) != 0:
            return ft.CupertinoBottomSheet(ft.Card(
                content=ft.Column(
                    [ft.ListView(
                        controls=self.create_attribute_list(user_attributes),
                        width=500,
                        spacing=10,
                        height=260 if height>260 else height,
                        padding=10,
                    )],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),width=550,height=300 if calc_height else height+40
            )
            ,height=300
            ,padding=ft.padding.only(top=6),on_dismiss=lambda e: self.close_options(e))
        else:
            return None

    def create_attribute_list(self,attributes=None):
        """
        Creates a text field for each user attribute and combines them into a single list.
        Allowed types are:
            int
            float
            string
            FilePath
            DirectoryPath
        """
        items = []
        for attribute_name in attributes:
            value = getattr(self.module, attribute_name)
            typ = type(value)
            if typ in (int, float, str):
                ref = ft.Ref[ft.Text]()
                items.append(ft.TextField(
                            label=attribute_name.removeprefix("user_"),
                            border_color=ft.colors.BLUE_ACCENT,
                            value=value,
                            ref=ref,
                            on_blur=lambda e,attr_name= attribute_name,reference=ref,type_atr = typ: self.on_change(e,attr_name,reference,type_atr),
                            height=60,
                        ))
            elif typ == FilePath:
                text_field = ft.TextField(
                    label=attribute_name.removeprefix("user_"),
                    border_color=ft.colors.BLUE_ACCENT,
                    value=format_directory_path(value.path,50),
                    height=60,
                    read_only=True,
                    disabled=True
                )
                file_picker = ft.FilePicker(on_result=lambda a,attr_name= attribute_name,text=text_field: self.on_select_file(a,attr_name,text))
                self.pipeline_gui.page.overlay.extend([file_picker])
                items.append(ft.Stack([text_field,ft.Container(
                                content=ft.IconButton(
                                    icon=ft.icons.UPLOAD_FILE,
                                    tooltip="Pick File",
                                    on_click=lambda e: file_picker.pick_files(allow_multiple=False),
                                ),
                                alignment=ft.alignment.top_right
                            ,right=10,top=5)
                    ]))
            elif typ == DirectoryPath:
                text_field = ft.TextField(
                    label=attribute_name.removeprefix("user_"),
                    border_color=ft.colors.BLUE_ACCENT,
                    value=format_directory_path(value.path, 50),
                    height=60,
                    read_only=True,
                    disabled=True
                )
                dir_picker = ft.FilePicker(
                    on_result=lambda a, attr_name=attribute_name, text=text_field: self.on_select_dir(a, attr_name,
                                                                                                       text))
                self.pipeline_gui.page.overlay.extend([dir_picker])
                items.append(ft.Stack([text_field, ft.Container(
                        content=ft.IconButton(
                            icon=ft.icons.FOLDER_OPEN,
                            tooltip="Open Directory",
                            on_click=lambda e: dir_picker.get_directory_path(),
                        ),
                        alignment=ft.alignment.top_right,right=10,top=5
                    )
                ]))
            else:
                raise ValueError(f"Unsupported 'user_' attribute file type: {typ}")
        return items

    def on_select_file(self,e,attr_name,text):
        """
        Handles if a file is selected.
        """
        if e.files is not None:
            setattr(self.module, attr_name, FilePath(e.files[0].path))
            text.value = format_directory_path(e.files[0].path,50)
            text.update()
            self.pipeline_gui.page.update()

    def on_select_dir(self,e,attr_name,text):
        """
        Handles if a directory is selected.
        """
        if e.path is not None:
            setattr(self.module, attr_name, FilePath(e.path))
            text.value = format_directory_path(e.path,50)
            text.update()
            self.pipeline_gui.page.update()

    def on_change(self,e,attr_name,reference,typ:type):
        """
        Handles changes to the attribute for different types.
        """
        try:
            setattr(self.module, attr_name, typ(e.control.value))
            reference.current.color = None
            self.pipeline_gui.page.update()
        except ValueError:
            attribute_name_without_prefix = attr_name.removeprefix("user_")
            self.pipeline_gui.page.snack_bar = ft.SnackBar(ft.Text(f"{attribute_name_without_prefix} only allows {typ.__name__}'s."))
            self.pipeline_gui.page.snack_bar.open = True
            reference.current.value = getattr(self.module, attr_name)
            reference.current.color = ft.colors.RED
            self.pipeline_gui.page.update()

    def open_options(self,e):
        e.control.page.open(self.module.settings)
        self.options_button.icon_color = ft.Colors.BLACK38
        self.options_button.update()

    def close_options(self,e):
        self.options_button.icon_color = ft.Colors.WHITE60
        self.options_button.update()

    def copy_module(self):
        self.copy_button.icon_color = ft.Colors.BLACK38
        self.copy_button.update()
        copy = self.pipeline_gui.add_module(ModuleType(type(self.module)),self.left+20,self.top+20)
        user_attributes = copy.module.get_user_attributes
        for attr_name in user_attributes:
            setattr(copy.module,attr_name,getattr(self.module, attr_name))
        if hasattr(copy.module, "_settings"):
            copy.module._settings = copy.generate_options_overlay()
        self.copy_button.icon_color = ft.Colors.WHITE60
        self.copy_button.update()



