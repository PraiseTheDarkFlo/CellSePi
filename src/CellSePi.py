from src.config_file import ConfigFile


class CellSePi:
    def __init__(self):
        super().__init__()
        self.config: ConfigFile = ConfigFile()
        self.segmentation_running = False
        self.segmentation_thread = None
        self.model_path = None
        self.readout_running = False
        self.readout_thread = None
        self.readout_path = None

        self.image_id = None
        self.channel_id = None

        self.readout = None

        self.adjusted_image_path = None
        self.image_paths = None #[image_id, different images sorted by channel]
        self.mask_paths = None

        self.working_directory = None

