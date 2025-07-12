import flet as ft
from src.cellsepi.backend.main_window.expert_mode.module import Module,Port

class DummyModule1(Module):
    def __init__(self):
        self._name = "test1"
        self._outputs = {
            "port1": Port("port1", int)
        }

    @property
    def name(self) -> str:
        return self._name

    @property
    def inputs(self) -> dict[str, Port]:
        return {}

    @property
    def outputs(self) -> dict[str, Port]:
        return self._outputs

    @property
    def gui(self) -> ft.Container:
        pass

    def run(self):
        result = 42 + 25
        self._outputs["port1"].data = result


class DummyModule2(Module):
    def __init__(self):
        self._name = "test2"
        self._inputs = {
            "port1": Port("port1", int)
        }
        self._outputs = {
            "port2": Port("port2", str)
        }
    @property
    def name(self) -> str:
        return self._name

    @property
    def inputs(self) -> dict[str, Port]:
        return self._inputs

    @property
    def outputs(self) -> dict[str, Port]:
        return self._outputs

    @property
    def gui(self) -> ft.Container:
        pass

    def run(self):
        port1 = self.inputs["port1"].data
        self.outputs["port2"].data = f"The resulting data is: {port1}"

class DummyModule3(Module):
    def __init__(self):
        self._name = "test3"
        self._inputs = {
            "port1": Port("port1", str),
        }
    @property
    def name(self) -> str:
        return self._name

    @property
    def inputs(self) -> dict[str, Port]:
        return self._inputs

    @property
    def outputs(self) -> dict[str, Port]:
        return {}

    @property
    def gui(self) -> ft.Container:
        pass

    def run(self):
        pass
class DummyModule4(Module):
    def __init__(self):
        self._name = "test4"
        self._inputs = {
            "port1": Port("port1", int),
            "port2": Port("port2", str),
            "port4": Port("port4", str,True),
            "port5": Port("port5", str,True),
        }
        self._outputs = {
            "port3": Port("port3", str),
        }
    @property
    def name(self) -> str:
        return self._name

    @property
    def inputs(self) -> dict[str, Port]:
        return self._inputs

    @property
    def outputs(self) -> dict[str, Port]:
        return self._outputs

    @property
    def gui(self) -> ft.Container:
        pass

    def run(self):
        result = self.inputs["port2"].data + " == " + str(self.inputs["port1"].data)
        self.outputs["port3"].data = result
