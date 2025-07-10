from cellsepi.backend.main_window.pipeline.module import Module
from typing import List

class Pipe:
    """
    Transfers the data from one module to another.
    """
    def __init__(self,source_module: Module,target_module: Module, ports: List[str]):
        self.source_module = source_module
        self.target_module = target_module
        self.ports = ports

    def run(self):
        for port in self.ports:
            if port not in self.source_module.outputs:
                raise KeyError(f"{port} is not in the outputs of Module: {self.source_module.name}")
            if port in self.target_module.inputs:
                raise KeyError(f"{port} is not in the inputs of Module: {self.source_module.name}")
            out_port = self.source_module.outputs[port]
            in_port = self.source_module.inputs[port]
            if out_port.data_type == in_port.data_type:
                in_port.data = out_port.data
            else:
                raise TypeError(
                    f"Type mismatch on port {port}, source_module provided {out_port.data_type}, output_module provided {in_port.data_type}!")