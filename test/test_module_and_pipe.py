import flet as ft
from typing import List
from src.cellsepi.backend.main_window.pipeline.module import Module,Port
from src.cellsepi.backend.main_window.pipeline.pipe import Pipe
import pytest

class TestModule1(Module):
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


class TestModule2(Module):
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

class TestModule3(Module):
    def __init__(self):
        self._name = "test3"
        self._inputs = {
            "port1": Port("port1", str)
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


def test_set_port_wrong():
    mod = TestModule1()
    with pytest.raises(TypeError):
        mod.outputs["port1"].data = "hi"


def test_set_port_right():
    mod = TestModule1()
    mod.outputs["port1"].data = 42
    assert  mod.outputs["port1"].data == 42 , "Something went wrong by setting the port data"

def test_pipe_wrong():
    mod1 = TestModule1()
    mod1.outputs["port1"].data = 42
    mod3 = TestModule3()
    pipe = Pipe(mod1, mod3)
    with pytest.raises(TypeError):
        pipe.run()

def test_pipe_right():
    mod1 = TestModule1()
    mod1.outputs["port1"].data = 42
    mod2 = TestModule2()
    pipe = Pipe(mod1, mod2)
    pipe.run()
    assert mod2.inputs["port1"].data == 42, "Something went wrong by transferring the data with the pipe"

def test_running_module_pipe():
    mod1 = TestModule1()
    mod2 = TestModule2()
    pipe = Pipe(mod1, mod2)
    pipeline = [mod1,pipe,mod2]
    for step in pipeline:
        step.run()
    assert mod1.outputs["port1"].data == 67, "Something went wrong by running the first module"
    assert mod2.inputs["port1"].data == 67, "Something went wrong by transferring the data with the pipe"
    assert mod2.outputs["port2"].data == "The resulting data is: 67" , "Something went wrong by running the second module"
