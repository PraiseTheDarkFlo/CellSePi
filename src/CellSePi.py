from src.config_file import ConfigFile


class CellSePi:
    def __init__(self):
        super().__init__()
        self.config: ConfigFile = ConfigFile()
        self.segmentation_running = False
        self.segmentation_thread = None
        self.readout_running = False
        self.readout_thread = None
        self.readout_path = None

        self.image_id = None
        self.channel_id = None
        self.image_view_update = True

        self.readout = None

        self.bit_depth = 16

        self.images = []
        self.image_paths = None
        self.mask_paths = None
        self.image_views = []

        self.working_directory = None


