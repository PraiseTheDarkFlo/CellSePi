from cellsepi.backend.main_window.pipeline.module import Module


class Pipe:
    """
    Transfers the data from one module to another.
    """
    def __init__(self,source_module: Module,target_module: Module):
        self.source_module = source_module
        self.target_module = target_module

    def run(self):
        for out_name, out_port in self.source_module.outputs.items():
            if out_name in self.target_module.inputs:
                in_port = self.target_module.inputs[out_name]
                if out_port.data_type == in_port.data_type:
                    in_port.data = out_port.data
                else:
                    raise TypeError(f"Type mismatch on port {out_name}, source_module provided {in_port.data_type}, output_module provided {out_port.data_type}!")
