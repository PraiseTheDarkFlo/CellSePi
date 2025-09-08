import json
import os
from pathlib import Path
from typing import List, Dict, Any

from jsonschema import validate, ValidationError

def load_schema(schema_path: str) -> dict:
    import json
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)

class PipelineStorage:
    def __init__(self,pipeline_gui):
        self.schema_name = "csp.schema.json"
        self.project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        self.schema_directory = os.path.join(self.project_root, self.schema_name)
        self.pipeline_gui = pipeline_gui
        self.version = "csp-1.0"
        self.schema = load_schema(schema_path=self.schema_directory)

    def save_pipeline(self,file_path:str= ""):
        modules: List[Dict[str, Any]] = []
        pipes: List[Dict[str, Any]] = []
        view = {"zoom": 1.0,"offset_x": 0.0,"offset_y": 0.0}

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

        try:
            validate(instance=pipeline_dict, schema=self.schema)
        except ValidationError as e:
            raise ValueError(f"Pipeline json doesn't match with: {e.message}")

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(pipeline_dict, f, indent=2, ensure_ascii=False)



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

        self.pipeline_gui.reset()
        self.pipeline_gui.load_pipeline(pipeline_dict)

