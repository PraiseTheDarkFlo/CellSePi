from itertools import chain

from cellsepi.backend.main_window.expert_mode.event_manager import EventManager
from cellsepi.backend.main_window.expert_mode.module import Module,Port
from cellsepi.backend.main_window.expert_mode.pipe import Pipe
from typing import List, Dict


class Pipeline:
    def __init__(self):
        self.modules: List[Module] = [] #running order
        self.module_map: Dict[str, Module] = {} #mapping for fast access to the modules
        self.pipes_in: Dict[str,List[Pipe]] = {} #dict[target,[Pipe]]
        self.pipes_out: Dict[str,List[Pipe]] = {} #dict[source,[Pipe]]
        self.event_manager: EventManager = EventManager()

    def add_module(self, module: Module) -> None:
        """
        Adds a module to the pipeline.

        Raises:
            ValueError: If a module with the same name already exists in the pipeline or the module itself is already added.
        """
        if any(mod.name == module.name for mod in self.modules):
            raise ValueError(f"Module name '{module.name}' already exists in the pipeline.")
        self.modules.append(module)
        self.module_map[module.name] = module
        self.pipes_in[module.name] = []
        self.pipes_out[module.name] = []

    def remove_module(self, module: Module) -> None:
        """
        Removes a module from the pipeline.
        Raises:
            RuntimeError: If the module is still connected to other modules.
        """
        if not self.is_disconnected(module.name):
            raise RuntimeError(f"Cannot remove module '{module.name}' from pipeline while connections to other modules still exists.")
        if module in self.modules:
            self.modules.remove(module)
            del self.module_map[module.name]
            del self.pipes_in[module.name]
            del self.pipes_out[module.name]


    def is_disconnected(self, module_name: str) -> bool:
        """
        Checks if a module has no connected modules.
        """
        return len(self.pipes_in[module_name]) == 0 and len(self.pipes_out[module_name]) == 0

    def remove_connection(self,source_name: str, target_name: str) -> None:
        """
        Removes a pipe between the source and target modules.
        Raises:
            ValueError: If a pipe between the source and target modules does not exist.
        """
        pipe = self.get_pipe(source_name, target_name)
        if pipe is None:
            raise ValueError(f"Pipe between source module '{source_name}' and target module '{target_name}' does not exist.")

        self.pipes_in[target_name].remove(pipe)
        self.pipes_out[source_name].remove(pipe)

    def get_pipe(self, source_name: str, target_name: str) -> Pipe | None:
        """
        Returns the pipe between source module and target module or if it does not exist it returns None.
        """
        for pipe in self.pipes_in.get(target_name, []):
            if pipe.source_module.name == source_name:
                return pipe
        return None

    def add_connection(self, pipe: Pipe) -> None:
        """
        Adds a pipe to the pipeline.
        Raises:
            ModuleNotFoundError: if the target or source module is not already added in the pipeline.
            ValueError: If a pipe between the target and source module exists already in the pipeline.
        """
        if pipe.source_module not in self.modules:
            raise ModuleNotFoundError(f"Source module '{pipe.source_module.name}' not found in the pipeline.")
        if pipe.target_module not in self.modules:
            raise ModuleNotFoundError(f"Target module '{pipe.target_module.name}' not found in the pipeline.")

        for existing_pipe in self.pipes_in[pipe.target_module.name]:
            if existing_pipe.source_module.name == pipe.source_module.name:
                raise ValueError(f"Pipe between source module '{pipe.source_module.name}' and target module '{pipe.target_module.name}' already exists.")

        self.pipes_in[pipe.target_module.name].append(pipe)
        self.pipes_out[pipe.source_module.name].append(pipe)

    def check_runnable(self) -> bool:
        """
        Checks if every modules inputs is satisfied.
        """
        for module in self.modules:
            module_pipes = self.pipes_in[module.name]
            delivered_ports = set(chain.from_iterable(pipe.ports for pipe in module_pipes))
            if not all(port_name in delivered_ports for port_name in module.get_mandatory_inputs()):
                return False
        return True

    def run(self):
        """
        Executes the steps of the Pipeline.
        Raises:
            RuntimeError: If one or more modules are not satisfied with their mandatory inputs.
        """
        if not self.check_runnable():
            raise RuntimeError(f"Pipeline is not runnable. One or more modules has no connection to all their mandatory inputs.")
        for module in self.modules:
            module.event_manager = self.event_manager
            module_pipes = self.pipes_in[module.name]
            for pipe in module_pipes:
                pipe.run()
            module.run()