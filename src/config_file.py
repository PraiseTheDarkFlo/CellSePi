import json
import os
import shutil


def load_config(file_directory):
    config_on_file = {}
    try:
        with open(file_directory, 'r') as file:
            config_on_file = json.load(file)
    except (json.JSONDecodeError, FileNotFoundError):
        config_on_file = create_default_config()
    return config_on_file

def create_default_config():
     return {
        "Profiles": {
            "Lif": {
                "bf_channel": "2",
                "mask_suffix": "_seg",
                "channel_prefix": "c",
                "diameter": "125.0"
                },
            "Tif": {
                "bf_channel": "1",
                "mask_suffix": "_seg",
                "channel_prefix": "c",
                "diameter": "250.0"
                }
            }
     }

class ConfigFile:
    def __init__(self,filename="config.json"):
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.file_directory = os.path.join(self.project_root, filename)
        self.config = load_config(self.file_directory)
        self.save_config()

    def save_config(self):
        with open(self.file_directory, 'w') as file:
            json.dump(self.config, file, indent=4)

    def update_config(self):
        self.config = load_config(self.file_directory)

    def add_profile(self, name:str, bf_channel: int, mask_suffix:str, channel_prefix:str, diameter: float):
        self.update_config()
        if not all([name, mask_suffix, channel_prefix]):
            raise ValueError("Name, mask_suffix, and channel_prefix must not be empty.")
        if diameter <= 0 and bf_channel <= 0:
            raise ValueError("diameter and bf_channel must be greater than 0.")
        if not name in self.config['Profiles']:
            self.config['Profiles'][name] = {
                "bf_channel": bf_channel,
                "mask_suffix": mask_suffix,
                "channel_prefix": channel_prefix,
                "diameter": diameter
            }
            self.save_config()
            return True
        else:
            return False

    def update_profile(self, name: str, bf_channel: int = None, mask_suffix: str = None,
                       channel_prefix: str = None, diameter: float = None):
        self.update_config()
        if name in self.config['Profiles']:
            if bf_channel is not None:
                if bf_channel <= 0:
                    raise ValueError("bf_channel must be greater than 0.")
                self.config['Profiles'][name]["bf_channel"] = bf_channel
            if mask_suffix is not None:
                if not mask_suffix:
                    raise ValueError("mask_suffix must not be empty.")
                self.config['Profiles'][name]["mask_suffix"] = mask_suffix
            if channel_prefix is not None:
                if not channel_prefix:
                    raise ValueError("channel_prefix must not be empty.")
                self.config['Profiles'][name]["channel_prefix"] = channel_prefix
            if diameter is not None:
                if diameter <= 0:
                    raise ValueError("diameter must be greater than 0.")
                self.config['Profiles'][name]["diameter"] = diameter
            self.save_config()

    def rename_profile(self,old_name: str,new_name: str):
        self.update_config()
        if not all([old_name,new_name]):
            raise ValueError("old_name, new_name must not be empty.")
        if old_name == new_name:
            return True
        elif old_name in self.config['Profiles'] and not new_name in self.config['Profiles']:
            self.config['Profiles'][new_name] = self.config['Profiles'].pop(old_name)
            self.save_config()
            return True
        else:
            return False

    def get_profile(self, name):
        self.update_config()
        if name in self.config['Profiles']:
            return self.config['Profiles'][name]

    def delete_profile(self, name: str):
        self.update_config()
        if name in self.config['Profiles']:
            del self.config['Profiles'][name]
            self.save_config()

    def clear_config(self):
        backup_filepath = os.path.join(self.project_root, 'config_backup.json')
        shutil.copy(self.file_directory, backup_filepath)
        open(self.file_directory, 'w').close()
        self.config = load_config(self.file_directory)

    def delete_config(self):
        backup_filepath = os.path.join(self.project_root, 'config_backup.json')
        shutil.copy(self.file_directory, backup_filepath)
        os.remove(self.file_directory)

    def restore_config(self):
        backup_filepath = os.path.join(self.project_root, 'config_backup.json')
        shutil.copy(backup_filepath, self.file_directory)
        self.config = load_config(self.file_directory)
        os.remove(backup_filepath)

