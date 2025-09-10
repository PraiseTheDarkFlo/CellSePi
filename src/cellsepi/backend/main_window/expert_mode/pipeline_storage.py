import json
import os
from pathlib import Path
from typing import List, Dict, Any

from jsonschema import validate, ValidationError

def load_schema(schema_path: str) -> dict:
    import json
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)

IGNORED_KEYS = {"view", "position"}

def get_major_dict(data):
    """Deletes the unimportant data for change comparison"""
    if isinstance(data, dict):
        return {k: get_major_dict(v) for k, v in data.items() if k not in IGNORED_KEYS}
    elif isinstance(data, list):
        return [get_major_dict(x) for x in data]
    else:
        return data


class PipelineStorage:
    def __init__(self,pipeline_gui):
        self.schema_name = "csp.schema.json"
        self.project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        self.schema_directory = os.path.join(self.project_root, self.schema_name)
        self.pipeline_gui = pipeline_gui
        self.version = "csp-1.0"
        self.schema = load_schema(schema_path=self.schema_directory)

    def save_as_pipeline(self,file_path:str= ""):
        pipeline_dict = self.generate_pipline_dict()

        self.pipeline_gui.pipeline_directory = Path(file_path).parent
        self.pipeline_gui.pipeline_dict = pipeline_dict
        self.pipeline_gui.pipeline_name = Path(file_path).stem

        try:
            validate(instance=pipeline_dict, schema=self.schema)
        except ValidationError as e:
            raise ValueError(f"Pipeline json doesn't match with: {e.message}")

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(pipeline_dict, f, indent=2, ensure_ascii=False)

    def save_pipeline(self):
        pipeline_dict = self.generate_pipline_dict()

        self.pipeline_gui.pipeline_dict = pipeline_dict

        file_path = str(self.pipeline_gui.pipeline_directory) + "/" + self.pipeline_gui.pipeline_name + ".csp"

        try:
            validate(instance=pipeline_dict, schema=self.schema)
        except ValidationError as e:
            raise ValueError(f"Pipeline json doesn't match with: {e.message}")

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(pipeline_dict, f, indent=2, ensure_ascii=False)

        return file_path

    def generate_pipline_dict(self):
        modules: List[Dict[str, Any]] = []
        pipes: List[Dict[str, Any]] = []
        view = {"zoom": 1.0, "offset_x": 0.0, "offset_y": 0.0}

        for module in self.pipeline_gui.modules.values():
            modules.append(module.to_dict())

        for pipe_list in self.pipeline_gui.pipeline.pipes_in.values():
            for pipe in pipe_list:
                pipes.append(pipe.to_dict())

        pipeline_dict = {
            "version": self.version,
            "modules": modules,
            "pipes": pipes,
            "view": view
        }

        return pipeline_dict

    def check_saved(self):
        """
        Checks if the pipeline is still saved.
        Ignores module positions and view.
        """
        if len(self.pipeline_gui.modules) == 0:
            return True

        if self.pipeline_gui.pipeline_dict == {}:
            return False

        new_pipeline_dict = get_major_dict(self.generate_pipline_dict())
        old_pipeline_dict = get_major_dict(self.pipeline_gui.pipeline_dict)
        return new_pipeline_dict==old_pipeline_dict


    def load_pipeline(self,file_path: str):
        filename = Path(file_path)
        pipeline_dict = {}

        if filename.suffix != ".csp":
            raise ValueError(f"The chosen file has not the right suffix: '{filename.suffix}' expected: '.csp'")

        if filename.exists():
            with filename.open("r", encoding="utf-8") as f:
                pipeline_dict = json.load(f)
        else:
            raise FileNotFoundError("Pipeline json doesn't exist")

        try:
            validate(instance=pipeline_dict, schema=self.schema)
        except ValidationError as e:
            raise ValueError(f"Pipeline json doesn't match with: {e.message}")

        self.pipeline_gui.pipeline_directory = filename.parent
        self.pipeline_gui.pipeline_name = filename.stem
        self.pipeline_gui.pipeline_dict = pipeline_dict
        self.pipeline_gui.reset()
        self.pipeline_gui.load_pipeline()

