import logging
import configobj

# Adapted from click_config_file.configobj_provider so that we can store the
# file path that the config was loaded from in order to log it later.

log = logging


class ConfigProvider:
    def __init__(self):
        self.file_path = None

    def __call__(self, file_path, cmd_name):
        self.file_path = file_path
        return configobj.ConfigObj(file_path, unrepr=True)
