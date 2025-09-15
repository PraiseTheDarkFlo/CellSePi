import math
import platform
from enum import Enum
import flet as ft

from cellsepi.backend.main_window.expert_mode.modules.batch_image_readout import BatchImageReadoutModule
from cellsepi.backend.main_window.expert_mode.modules.batch_image_seg import BatchImageSegModule
from cellsepi.backend.main_window.expert_mode.modules.project_3d_to_2d import Project3dTo2d
from cellsepi.backend.main_window.expert_mode.modules.read_lif import ReadLif
from cellsepi.backend.main_window.expert_mode.modules.read_tif import ReadTif
from cellsepi.backend.main_window.expert_mode.modules.review import Review

BUILDER_WIDTH = 1000
BUILDER_HEIGHT = 400
MODULE_WIDTH = 235
MODULE_HEIGHT = 80
SPACING_X = 10
SPACING_Y = 20
SHOWROOM_PADDING_X = 20
SHOWROOM_MODULE_COUNT = 4
ARROW_LENGTH = 23
ARROW_ANGLE = math.radians(40)
ARROW_PADDING = -1
ARROW_COLOR = ft.Colors.CYAN_900
INVALID_COLOR = ft.Colors.BLACK54
VALID_COLOR = ft.Colors.WHITE30
MENU_COLOR = ft.Colors.BLACK54
DISABLED_BUTTONS_COLOR = ft.Colors.BLACK12
USER_OPTIONS_LIMIT = 3
ZOOM_VALUE = 0.20
BOTTOM_SPACING = 20 if not platform.system() == "Linux" else 40
MAIN_ACTIVE_COLOR = ft.Colors.WHITE60
THROTTLE_UPDATE_LINES = 0.036 #~30FPS

class ModuleType(Enum):
    BATCH_IMAGE_READOUT = BatchImageReadoutModule
    BATCH_IMAGE_SEG = BatchImageSegModule
    READ_LIF = ReadLif
    READ_TIF = ReadTif
    PROJECTION_3D_TO_2D = Project3dTo2d
    REVIEW = Review

