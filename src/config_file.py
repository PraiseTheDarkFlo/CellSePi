import json
import os
import shutil
import time


class DeletionForbidden(Exception):
    pass

#return the current config_file
#try 5 times to read before resetting the data
def load_config(file_directory):
    for _ in range(5):
        try:
            with open(file_directory, 'r') as file:
                return json.load(file)
        except json.JSONDecodeError:
            time.sleep(0.1)
    return create_default_config()

#default config_file used when the config is empty or is deleted
def create_default_config():
     return {
        "Profiles": {
            "Lif": {
                "bf_channel": 2,
                "mask_suffix": "_seg",
                "channel_prefix": "c",
                "diameter": 125.0
                },
            "Tif": {
                "bf_channel": 1,
                "mask_suffix": "_seg",
                "channel_prefix": "c",
                "diameter": 250.0
                }
            },
            "Selected Profile": {
                "name": "Lif"
            }
     }

#Class that manges the config file
class ConfigFile:
    def __init__(self,filename="config.json"):
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.file_directory = os.path.join(self.project_root, filename)
        self.config = load_config(self.file_directory)

    def save_config(self):
        with open(self.file_directory, 'w') as file:
            json.dump(self.config, file, indent=4)

    #add the profile with the parameter, but also checks if the inputs are fine
    #returns error if parameter is not fine, returns True if it worked and return False
    #if the name is already taken
    def add_profile(self, name:str, bf_channel: int, mask_suffix:str, channel_prefix:str, diameter: float):
        if not all([name, mask_suffix, channel_prefix]):
            raise ValueError("Name, mask_suffix, and channel_prefix must not be empty.")
        if diameter <= 0 and bf_channel <= 0:
            raise ValueError("diameter and bf_channel must be greater than 0.")
        if not name in self.config['Profiles']:
            self.config["Profiles"][name] = {
                "bf_channel": bf_channel,
                "mask_suffix": mask_suffix,
                "channel_prefix": channel_prefix,
                "diameter": diameter
            }
            self.save_config()
            return True
        else:
            return False

    #updates the profile that is named in the name parameter,
    #you can update all or only some parameters if you try to update every parameter gets check if it's fine
    #returns error when a parameter is not fine
    def update_profile(self, name: str, bf_channel: int = None, mask_suffix: str = None,
                       channel_prefix: str = None, diameter: float = None):
        if name in self.config["Profiles"]:
            if bf_channel is not None:
                if bf_channel <= 0:
                    raise ValueError("bf_channel must be greater than 0.")
                self.config["Profiles"][name]["bf_channel"] = bf_channel
            if mask_suffix is not None:
                if not mask_suffix:
                    raise ValueError("mask_suffix must not be empty.")
                self.config["Profiles"][name]["mask_suffix"] = mask_suffix
            if channel_prefix is not None:
                if not channel_prefix:
                    raise ValueError("channel_prefix must not be empty.")
                self.config["Profiles"][name]["channel_prefix"] = channel_prefix
            if diameter is not None:
                if diameter <= 0:
                    raise ValueError("diameter must be greater than 0.")
                self.config["Profiles"][name]["diameter"] = diameter
            self.save_config()

    #rename check if the names are fine
    #and only update it when the new != old and returns false if the new name is already taken
    def rename_profile(self,old_name: str,new_name: str):
        if not all([old_name,new_name]):
            raise ValueError("old_name, new_name must not be empty.")
        elif old_name == new_name:
            return True
        elif old_name in self.config["Profiles"] and new_name not in self.config["Profiles"]:
            self.config["Profiles"][new_name] = self.config["Profiles"].pop(old_name)
            self.save_config()
            if old_name == self.get_selected_profile_name():
                self.select_profile(new_name)
            return True
        else:
            return False

    def get_profile(self, name):
        if name in self.config["Profiles"]:
            return self.config["Profiles"][name]

    #delte the profile
    #size of profiles must be minimum 1
    #throw error if error would minimize the profiles to 1 or smaller or if the name is not in the profiles
    def delete_profile(self, name: str):
        if name in self.config["Profiles"] and len(self.config["Profiles"]) > 1:
            del self.config["Profiles"][name]
            if self.config["Selected Profile"]["name"] == name:
                first_key = next(iter(self.config["Profiles"]))
                self.config["Selected Profile"]["name"] = first_key
            self.save_config()
        else:
            raise DeletionForbidden


    def select_profile(self,name: str):
        if not name:
            raise ValueError("name must not be empty.")
        elif name in self.config["Profiles"]:
            self.config["Selected Profile"]["name"] = name
            self.save_config()

    def get_selected_profile_name(self):
        if self.config["Selected Profile"]["name"] is not None:
            return self.config["Selected Profile"]["name"]
        else:
            first_key = next(iter(self.config["Profiles"]))
            self.config["Selected Profile"]["name"] = first_key
            return first_key

    #translates name to idx
    def name_to_index(self, name: str):
        profiles = list(self.config["Profiles"].keys())
        if name in profiles:
            return profiles.index(name)
        else:
            raise ValueError("Profile with that name does not exists")

    #translates idx to the name
    def index_to_name(self, index: int):
        profiles = list(self.config["Profiles"].keys())
        if 0 <= index < len(profiles):
            return profiles[index]
        else:
            raise ValueError("Didnt find a profile at this index")

    #------------------------------------------
    #getter for the selected profiles Attributes

    def get_selected_profile(self):
        name = self.get_selected_profile_name()
        return self.config["Profiles"][name]

    def get_bf_channel(self):
        profile = self.get_selected_profile()
        return int(profile["bf_channel"])

    def get_mask_suffix(self):
        profile = self.get_selected_profile()
        return profile["mask_suffix"]

    def get_channel_prefix(self):
        profile = self.get_selected_profile()
        return profile["channel_prefix"]

    def get_diameter(self):
        profile = self.get_selected_profile()
        return float(profile["diameter"])

    #-----------------------------------------------------
    #only for test_config
    def clear_config(self):
        backup_filepath = os.path.join(self.project_root, "config_backup.json")
        shutil.copy(self.file_directory, backup_filepath)
        open(self.file_directory, 'w').close()
        self.config = load_config(self.file_directory)

    def delete_config(self):
        backup_filepath = os.path.join(self.project_root, "config_backup.json")
        shutil.copy(self.file_directory, backup_filepath)
        os.remove(self.file_directory)

    def restore_config(self):
        backup_filepath = os.path.join(self.project_root, "config_backup.json")
        shutil.copy(backup_filepath, self.file_directory)
        self.config = load_config(self.file_directory)
        os.remove(backup_filepath)
