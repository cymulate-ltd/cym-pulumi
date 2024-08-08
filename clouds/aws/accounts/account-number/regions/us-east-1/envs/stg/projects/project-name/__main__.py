# use this to add the components module
import sys; sys.path.append('../../../../../../../../../../')

import os
from utils.shared import GlobalUtils

class Main:

    config = {}

    def __init__(self):
        dir_path = os.path.dirname(os.path.abspath(__file__))
        self.config = GlobalUtils.merge_yaml_files(GlobalUtils.get_all_config_paths(dir_path))
        
Main()
