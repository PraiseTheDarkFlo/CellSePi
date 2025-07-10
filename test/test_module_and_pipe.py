import flet as ft
from src.cellsepi.backend.main_window.pipeline.module import Module,Port
from src.cellsepi.backend.main_window.pipeline.pipe import Pipe
import pytest

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
            "port2": Port("port2", str)
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


def test_set_port_wrong():
    mod = DummyModule1()
    with pytest.raises(TypeError):
        mod.outputs["port1"].data = "hi"


def test_set_port_right():
    mod = DummyModule1()
    mod.outputs["port1"].data = 42
    assert  mod.outputs["port1"].data == 42 , "Something went wrong when setting the port data"

def test_pipe_wrong_type_mod1():
    mod1 = DummyModule1()
    mod3 = DummyModule3()
    pipe = Pipe(mod1, mod3, ["port1"])
    with pytest.raises(KeyError):
        pipe.run()

def test_pipe_source_without_port():
    mod1 = DummyModule1()
    mod1._outputs = {}
    mod3 = DummyModule3()
    pipe = Pipe(mod1, mod3, ["port1"])
    with pytest.raises(KeyError):
        pipe.run()

def test_pipe_target_without_port():
    mod1 = DummyModule1()
    mod1.outputs["port1"].data = 42
    mod3 = DummyModule3()
    mod3._outputs = {}
    pipe = Pipe(mod1, mod3, ["port1"])
    with pytest.raises(KeyError):
        pipe.run()

def test_pipe_right():
    mod1 = DummyModule1()
    mod1.outputs["port1"].data = 42
    mod2 = DummyModule2()
    pipe = Pipe(mod1, mod2,["port1"])
    pipe.run()
    assert mod2.inputs["port1"].data == 42, "Something went wrong when transferring the data with the pipe"

def test_running_module_pipe():
    mod1 = DummyModule1()
    mod2 = DummyModule2()
    pipe = Pipe(mod1, mod2,["port1"])
    pipeline = [mod1,pipe,mod2]
    for step in pipeline:
        step.run()
    assert mod1.outputs["port1"].data == 67, "Something went wrong when running the first module"
    assert mod2.inputs["port1"].data == 67, "Something went wrong when transferring the data with the pipe"
    assert mod2.outputs["port2"].data == "The resulting data is: 67" , "Something went wrong by running the second module"

def test_n_to_one_module():
    mod1 = DummyModule1()
    mod2 = DummyModule2()
    mod4 = DummyModule4()
    pipe1 = Pipe(mod1, mod2,["port1"])
    pipe2 = Pipe(mod1, mod4,["port1"])
    pipe3 = Pipe(mod2, mod4,["port2"])
    pipeline = [mod1, pipe1, mod2, pipe2, pipe3, mod4]
    for step in pipeline:
        step.run()
    assert mod1.outputs["port1"].data == 67, "Something went wrong when running the first module"
    assert mod2.inputs["port1"].data == 67, "Something went wrong when transferring the data with the pipe from m1 to m2"
    assert mod2.outputs["port2"].data == "The resulting data is: 67", "Something went wrong when running the second module"
    assert mod4.inputs["port2"].data == "The resulting data is: 67", "Something went wrong when transferring the data with the pipe from the m1 to m4"
    assert mod4.inputs["port1"].data == 67, "Something went wrong when transferring the data with the pipe from m1 to m4"
    assert mod4.outputs["port3"].data == "The resulting data is: 67 == 67", "Something went wrong when running the fourth module"