import math
from collections import deque
from typing import List

import flet as ft

from cellsepi.backend.main_window.expert_mode.listener import OnPipelineChangeEvent
from cellsepi.backend.main_window.expert_mode.pipe import Pipe
from cellsepi.backend.main_window.expert_mode.pipeline import Pipeline
from cellsepi.frontend.main_window.expert_mode.expert_constants import *
from cellsepi.frontend.main_window.expert_mode.gui_lines import LinesGUI
from cellsepi.frontend.main_window.expert_mode.gui_module import ModuleGUI


class PipelineGUI(ft.Stack):
    def __init__(self,page:ft.Page):
        super().__init__()
        self.controls = []
        self.pipeline = Pipeline()
        self.modules_executed = 0
        self.module_running_count = 0
        self.loading = False
        self.interactive_view = None
        self.pipeline_name = "NewPipeline"
        self.pipeline_directory = ""
        self.pipeline_dict = {} #last saved pipeline dict
        self.page = page
        self.modules = {} #identiefierer is the module_id
        self.show_room_size = len(ModuleType) if len(ModuleType) < SHOWROOM_MODULE_COUNT else SHOWROOM_MODULE_COUNT
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

    def reset(self):
        self.loading = True
        for module in list(self.modules.values()):
            module.remove_module()
        self.pipeline.run_order = deque()
        self.pipeline.executing = ""
        self.pipeline.running = False
        self.update()
        self.loading = False

    def load_pipeline(self):
        self.loading = True
        for module_dict in self.pipeline_dict["modules"]:
            type_map = {mt.value.gui_config().name: mt for mt in ModuleType}
            self.add_module(module_type=type_map[module_dict["module_name"]], x=module_dict["position"]["x"], y=module_dict["position"]["y"], module_id=module_dict["module_id"],module_dict=module_dict)

        for pipe in self.pipeline_dict["pipes"]:
            source = pipe["source"]
            target = pipe["target"]
            ports= pipe["ports"]
            self.add_connection(self.modules[source],self.modules[target],ports)

        offset_x = self.pipeline_dict["view"]["offset_x"]
        offset_y = self.pipeline_dict["view"]["offset_y"]
        scale = self.pipeline_dict["view"]["scale"]
        self.interactive_view.set_transformation_data(offset_x=offset_x, offset_y=offset_y, scale=scale)

        self.page.open(
            ft.SnackBar(ft.Text(f"Pipeline successfully loaded.", color=ft.Colors.WHITE), bgcolor=ft.Colors.GREEN))
        self.page.update()
        self.loading = False
        self.pipeline.event_manager.notify(OnPipelineChangeEvent(f"Pipeline {self.pipeline_name} loaded."))

    def check_all_deletable(self):
        for module in self.modules.values():
            if self.check_deletable(module):
                module.delete_button.visible = True
                module.delete_button.update()
            else:
                module.delete_button.visible = False
                module.delete_button.update()

    def check_deletable(self,module:ModuleGUI):
        if  module.name in self.pipeline.run_order or module.name == self.pipeline.executing:
            return False

        return all(not(pipe.target_module.module_id in self.pipeline.run_order or pipe.target_module.module_id == self.pipeline.executing) for pipe in self.pipeline.pipes_out[module.name])

    def add_connection(self,source_module_gui,target_module_gui,ports: List[str]):
        ports_copy = list(ports)
        self.pipeline.add_connection(pipe=Pipe(source_module_gui.module, target_module_gui.module, ports_copy))
        self.lines_gui.update_line(source_module_gui, target_module_gui,ports)
        self.lines_gui.update_gui()
        self.update_all_port_icons()

    def expand_connection(self,pipe:Pipe,ports:List[str]):
        ports_copy = list(ports)
        self.pipeline.expand_connection(pipe,ports_copy)
        self.lines_gui.update_line(self.modules[pipe.source_module.module_id], self.modules[pipe.target_module.module_id], pipe.ports)
        self.lines_gui.update_gui()
        self.update_all_port_icons()

    def remove_connection(self,source_module_gui,target_module_gui):
        self.pipeline.remove_connection(source_module_gui.name,target_module_gui.name)
        self.lines_gui.remove_line(source_module_gui, target_module_gui)
        self.update_all_port_icons()
        self.check_for_valid_all_modules()

    def add_show_room_module(self,module_type:ModuleType,x:float,y:float,visible:bool=True,show_room_id:int=None):
        module_gui = ModuleGUI(self, module_type, x, y,True,visible,id_number=show_room_id)
        self.page_stack.controls.insert(2,module_gui)
        return module_gui

    def refill_show_room(self,module_gui:ModuleGUI,visible:bool=True,index:int=None,show_room_id:int=None):
        new_module_gui = ModuleGUI(self, module_gui.module_type, x=SPACING_X + SHOWROOM_PADDING_X / 2, y=module_gui.show_offset_y, show_mode=True, visible=visible, index=index,id_number=show_room_id)
        self.page_stack.controls.insert(3,new_module_gui)
        self.page_stack.update()
        self.update_all_port_icons()

    def build_show_room(self,page_stack:ft.Stack):
        self.page_stack = page_stack
        x = SPACING_X + SHOWROOM_PADDING_X / 2
        y = SPACING_Y
        self.show_room_container = ft.Container(top=y - SPACING_Y / 2, left=SPACING_X, width=MODULE_WIDTH + SHOWROOM_PADDING_X, height=(self.show_room_size * MODULE_HEIGHT) + (self.show_room_size * SPACING_Y), bgcolor=MENU_COLOR, border_radius=ft.border_radius.all(10),blur=10)
        self.page_stack.controls.insert(1,self.show_room_container)
        self.show_room_max_page_number = math.ceil(len(ModuleType) / SHOWROOM_MODULE_COUNT)
        for i,module_type in enumerate(ModuleType):
            visible = i < SHOWROOM_MODULE_COUNT
            y_module = y+ (MODULE_HEIGHT + SPACING_Y) * (i%SHOWROOM_MODULE_COUNT)
            self.add_show_room_module(module_type,x,y_module,visible,-1)
            self.add_show_room_module(module_type,x,y_module,visible,-2)

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

    def add_module(self,module_type: ModuleType,x: float = None,y: float = None,module_id: str = None,module_dict:dict=None):
        id_number = int(module_id.removeprefix(module_type.value.gui_config().name)) if module_id is not None else None
        module_gui = ModuleGUI(self,module_type,x,y,id_number=id_number,module_dict=module_dict)
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
        gui_module = self.modules.pop(module_id)
        self.controls.remove(gui_module)
        self.pipeline.remove_module(gui_module.module)
        self.update()

    def toggle_all_module_detection(self,module_id: str):
        self.source_module = module_id
        self.transmitting_ports = []
        for module in self.modules.values():
            if module.name != module_id:
                module.toggle_detection()
                self.update()

    def toggle_all_stuck_in_running(self):
        for module in self.modules.values():
            self.lines_gui.update_delete_buttons(module)
            module.enable_tools()
            module.start_button.visible = True
            module.start_button.update()
            module.delete_button.visible = True
            module.delete_button.update()
            module.pause_button.visible = False
            module.pause_button.update()
            module.waiting_button.visible = False
            module.waiting_button.update()
        self.check_for_valid_all_modules()

    def check_for_valid_all_modules(self):
        for target_module_gui in self.modules.values():
            self.check_for_valid(target_module_gui.name)

    def check_for_valid(self,module_id: str):
        target_module_gui = self.modules[module_id]
        if (target_module_gui.name not in self.pipeline.run_order and target_module_gui.name != self.pipeline.executing) or not self.pipeline.running:
            if target_module_gui.name != self.source_module:
                valid = True
                existing_pipe = self.pipeline.check_connections(
                    self.source_module, target_module_gui.name) if self.source_module != "" else None
                if existing_pipe is None:
                    valid = True
                elif any(port in existing_pipe.ports for port in self.transmitting_ports) or existing_pipe.source_module.module_id != self.source_module or existing_pipe.target_module.module_id != target_module_gui.name:
                    valid = False
                if all(k in target_module_gui.module.inputs for k in
                       self.transmitting_ports) and self.transmitting_ports != [] and valid and not (
                self.pipeline.check_ports_occupied(target_module_gui.name, self.transmitting_ports)):
                    target_module_gui.set_valid()
                else:
                    target_module_gui.set_invalid()

    def update_all_port_icons(self):
        for module_gui in self.modules.values():
            module_gui.update_port_icons()
