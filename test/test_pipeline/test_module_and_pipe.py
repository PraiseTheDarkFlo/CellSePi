from test.test_pipeline.dummy_modules import *
from src.cellsepi.backend.main_window.expert_mode.pipe import Pipe
import pytest

def test_set_port_wrong():
    mod = DummyModule1()
    with pytest.raises(TypeError):
        mod.outputs["port1"].data = "hi"

def test_set_port_right():
    mod = DummyModule1()
    mod.outputs["port1"].data = 42
    assert  mod.outputs["port1"].data == 42 , "Something went wrong when setting the port data"

def test_pipe_same_modules():
    mod1 = DummyModule1()
    with pytest.raises(ValueError):
        Pipe(mod1,mod1,["Port1"])

def test_pipe_same_names():
    mod1 = DummyModule1()
    mod2 = DummyModule2()
    mod2._name = mod1.name
    with pytest.raises(ValueError):
        Pipe(mod1,mod2,["Port1"])

def test_pipe_wrong_type_mod1():
    mod1 = DummyModule1()
    mod3 = DummyModule3()
    pipe = Pipe(mod1, mod3, ["port1"])
    with pytest.raises(TypeError):
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
    mod3._inputs = {}
    pipe = Pipe(mod1, mod3, ["port1"])
    with pytest.raises(KeyError):
        pipe.run()

def test_correct_pipe():
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

def test_find_mandatory_inputs():
    mod4 = DummyModule4()
    mandatory_inputs = mod4.get_mandatory_inputs()
    assert mandatory_inputs == ["port1", "port2"], "Something went wrong when getting the mandatory inputs"

def test_find_no_mandatory_inputs():
    mod1 = DummyModule1()
    mandatory_inputs = mod1.get_mandatory_inputs()
    assert mandatory_inputs == [], "Something went wrong when getting the mandatory inputs"
