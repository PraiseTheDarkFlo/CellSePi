import math
from enum import Enum
import flet as ft

from cellsepi.backend.main_window.expert_mode.modules.batch_image_readout import BatchImageReadoutModule
from cellsepi.backend.main_window.expert_mode.modules.batch_image_seg import BatchImageSegModule
from cellsepi.backend.main_window.expert_mode.modules.read_lif_tif import ReadLifTif

BUILDER_WIDTH = 1000
BUILDER_HEIGHT = 400
MODULE_WIDTH = 235
MODULE_HEIGHT = 80
SHOWROOM_PADDING_X = 20
SHOWROOM_PADDING_Y = 20
ARROW_LENGTH = 23
ARROW_ANGLE = math.radians(40)
ARROW_PADDING = -1
ARROW_COLOR = ft.Colors.CYAN_900
INVALID_COLOR = ft.Colors.BLACK54
VALID_COLOR = ft.Colors.WHITE30

class ModuleType(Enum):
    BATCH_IMAGE_READOUT = BatchImageReadoutModule
    BATCH_IMAGE_SEG = BatchImageSegModule
    READ_LIF_TIF = ReadLifTif
