from enum import Enum

from cellsepi.backend.main_window.expert_mode.modules.batch_image_readout import BatchImageReadoutModule
from cellsepi.backend.main_window.expert_mode.modules.batch_image_seg import BatchImageSegModule
from cellsepi.backend.main_window.expert_mode.modules.read_lif_tif import ReadLifTif

BUILDER_WIDTH = 1000
BUILDER_HEIGHT = 500
MODULE_WIDTH = 235
MODULE_HEIGHT = 80

class ModuleType(Enum):
    BATCH_IMAGE_READOUT = BatchImageReadoutModule
    BATCH_IMAGE_SEG = BatchImageSegModule
    READ_LIF_TIF = ReadLifTif
