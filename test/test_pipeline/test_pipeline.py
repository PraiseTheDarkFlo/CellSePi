from torch._dynamo.replay_record import DummyModule

from test.test_pipeline.dummy_modules import *
from src.cellsepi.backend.main_window.expert_mode.pipe import Pipe
from src.cellsepi.backend.main_window.expert_mode.pipeline import Pipeline

import pytest


@pytest.fixture
def two_module_pipeline():
    pipeline = Pipeline()
    mod1 = DummyModule1()
    mod2 = DummyModule2()
    pipeline.add_module(mod1)
    pipeline.add_module(mod2)
    pipe = Pipe(mod1, mod2, ["port1"])
    pipeline.add_connection(pipe)
    assert pipeline.modules == [mod1, mod2], "Something went wrong when adding the modules to the pipeline"
    assert pipeline.pipes_in == {"test1": [],
                                 "test2": [pipe]}, "Something went wrong when adding the pipes to the pipeline"
    assert pipeline.pipes_out == {"test1": [pipe],
                                  "test2": []}, "Something went wrong when adding the pipes to the pipeline"
    yield pipeline

def test_add_module():
    pipeline = Pipeline()
    mod1 = DummyModule1()
    pipeline.add_module(mod1)
    assert pipeline.modules == [mod1], "Something went wrong when adding a module to the pipeline"

def test_add_module_same_names():
    pipeline = Pipeline()
    mod1 = DummyModule1()
    pipeline.add_module(mod1)
    with pytest.raises(ValueError):
        pipeline.add_module(mod1)

def test_add_connection(two_module_pipe):
    pipeline = Pipeline()
    mod1 = DummyModule1()
    mod2 = DummyModule2()
    pipeline.add_module(mod1)
    pipeline.add_module(mod2)
    pipe = Pipe(mod1, mod2,["port1"])
    pipeline.add_connection(pipe)
    assert pipeline.modules == [mod1,mod2], "Something went wrong when adding the modules to the pipeline"
    assert pipeline.pipes_in == {"test1":[],"test2":[pipe]}, "Something went wrong when adding the pipes to the pipeline"
    assert pipeline.pipes_out == {"test1":[pipe],"test2":[]}, "Something went wrong when adding the pipes to the pipeline"

def test_add_connection_source_not_added():
    pipeline = Pipeline()
    mod1 = DummyModule1()
    mod2 = DummyModule2()
    pipeline.add_module(mod2)
    pipe = Pipe(mod1, mod2,["port1"])
    with pytest.raises(ModuleNotFoundError):
        pipeline.add_connection(pipe)

def test_add_connection_target_not_added():
    pipeline = Pipeline()
    mod1 = DummyModule1()
    mod2 = DummyModule2()
    pipeline.add_module(mod1)
    pipe = Pipe(mod1, mod2,["port1"])
    with pytest.raises(ModuleNotFoundError):
        pipeline.add_connection(pipe)

def test_add_connection_already_added(two_module_pipeline):
    with pytest.raises(ValueError):
        two_module_pipeline.add_connection(two_module_pipeline.get_pipe("test1","test2"))

def test_remove_connection_with_error(two_module_pipeline):
    with pytest.raises(ValueError):
        two_module_pipeline.remove_connection("test1", "test2")

def test_remove_connection_valid(two_module_pipeline):
    two_module_pipeline.remove_connection("test1", "test2")
    assert two_module_pipeline.pipes_in == {"test1":[],"test2":[]}, "Something went wrong when removing the pipe from the pipeline"
    assert two_module_pipeline.pipes_out == {"test1":[],"test2":[]}, "Something went wrong when removing the pipes from the pipeline"

def test_remove_module_with_error(two_module_pipeline):
    with pytest.raises(RuntimeError):
        two_module_pipeline.remove_module(two_module_pipeline.module_map["test1"])

def test_remove_module_valid(two_module_pipeline):
    two_module_pipeline.remove_connection("test1", "test2")
    assert two_module_pipeline.pipes_in == {"test1": [],
                                            "test2": []}, "Something went wrong when removing the pipe from the pipeline"
    assert two_module_pipeline.pipes_out == {"test1": [],
                                             "test2": []}, "Something went wrong when removing the pipes from the pipeline"
    two_module_pipeline.remove_module(two_module_pipeline.module_map["test1"])
    assert two_module_pipeline.module_map == {"test2": two_module_pipeline.module_map["test2"],}, "Something went wrong when removing the pipe from the pipeline"
    assert two_module_pipeline.modules == [two_module_pipeline.module_map["test2"]], "Something went wrong when removing the module from the pipeline"
    assert two_module_pipeline.pipes_in == {"test2": [],}, "Something went wrong when removing the pipe from the pipeline"
    assert two_module_pipeline.pipes_out == {
        "test2": [], }, "Something went wrong when removing the pipe from the pipeline"

def test_run_with_false_runnable(two_module_pipeline):
    two_module_pipeline.remove_connection("test1", "test2")
    with pytest.raises(RuntimeError):
        two_module_pipeline.run()

def test_run_valid(two_module_pipeline):
    two_module_pipeline.run()
    assert two_module_pipeline.module_map["test1"].outputs["port1"].data == 67, "Something went wrong when running the pipeline"
    assert two_module_pipeline.module_map["test2"].inputs["port1"].data == 67, "Something went wrong when running the pipeline"
    assert two_module_pipeline.module_map["test2"].outputs[
               "port2"].data == "The resulting data is: 67", "Something went wrong when running the pipeline"

def test_run_n_to_one_module_valid(two_module_pipeline):
    mod1 = two_module_pipeline.module_map["test1"]
    mod2 = two_module_pipeline.module_map["test2"]
    mod4 = DummyModule4()
    two_module_pipeline.add_module(mod4)
    pipe2 = Pipe(mod1, mod4, ["port1"])
    pipe3 = Pipe(mod2, mod4, ["port2"])
    two_module_pipeline.add_connection(pipe2)
    two_module_pipeline.add_connection(pipe3)
    two_module_pipeline.run()
    assert mod1.outputs["port1"].data == 67, "Something went wrong when running the first module"
    assert mod2.inputs[
               "port1"].data == 67, "Something went wrong when transferring the data with the pipe from m1 to m2"
    assert mod2.outputs[
               "port2"].data == "The resulting data is: 67", "Something went wrong when running the second module"
    assert mod4.inputs[
               "port2"].data == "The resulting data is: 67", "Something went wrong when transferring the data with the pipe from the m1 to m4"
    assert mod4.inputs[
               "port1"].data == 67, "Something went wrong when transferring the data with the pipe from m1 to m4"
    assert mod4.outputs[
               "port3"].data == "The resulting data is: 67 == 67", "Something went wrong when running the fourth module"
