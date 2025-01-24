import asyncio
import multiprocessing

import flet as ft
from flet_core import BoxShape

from .gui_options import Options
from .gui_segmentation import GUISegmentation
from .drawing.gui_drawing import open_qt_window
from .gui_canvas import Canvas
from .gui_config import GUIConfig
from .gui_directory import DirectoryCard
from src.CellSePi import CellSePi
from src.mask import Mask
from .gui_mask import error_banner,handle_image_switch_mask_on
from ..avg_diameter import AverageDiameter
from ..image_tuning import ImageTuning, AutoImageTuning


class GUI:
    """
    Class GUI to handle the complete GUI and their attributes, also contains the CellSePi class and updates their attributes
    """
    def __init__(self,page: ft.Page):
        self.csp: CellSePi = CellSePi()
        self.page = page
        self.directory = DirectoryCard(self)
        self.switch_mask = ft.Switch(label="Mask", value=False)
        self.queue = multiprocessing.Queue()
        self.start_drawing_window()
        self.drawing_button= ft.ElevatedButton(text="Drawing Tools", icon="brush_rounded",on_click=lambda e: self.set_queue_drawing_window(),disabled=True)
        self.page.window.width = 1400
        self.page.window.height = 800
        self.page.window.center()
        self.page.window.min_width = self.page.window.width
        self.page.window.min_height = self.page.window.height
        self.page.title = "CellSePi"
        self.canvas = Canvas()
        self.op = Options(page=self.page,csp=self.csp)
        gui_config = GUIConfig(self)
        self.gui_config = gui_config.create_profile_container()
        self.segmentation = GUISegmentation(self)
        seg_card,start_button,open_button,progress_bar,progress_bar_text = self.segmentation.create_segmentation_card()
        self.ready_to_start = False
        self.segmentation_card = seg_card
        self.open_button = open_button
        self.start_button = start_button
        self.progress_bar = progress_bar
        self.progress_bar_text = progress_bar_text
        self.mask=Mask(self.csp)
        self.image_tuning = ImageTuning(self)
        self.brightness_slider = ft.Slider(
            min=0, max=2.0, value=1.0, disabled= True,
            on_change=lambda e: asyncio.run(self.image_tuning.update_main_image_async())
        )
        self.contrast_slider = ft.Slider(
            min=0, max=2.0, value=1.0, disabled= True,
            on_change=lambda e: asyncio.run(self.image_tuning.update_main_image_async())
        )
        self.auto_image_tuning = AutoImageTuning(self)
        self.auto_brightness_contrast = ft.IconButton(icon=ft.Icons.AUTO_FIX_HIGH,icon_color=ft.Colors.GREY_700,style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=12),
                ),on_click=lambda e: self.auto_image_tuning.pressed(e),tooltip="Auto brightness and contrast")
        self.brightness_icon = ft.Icon(name=ft.icons.SUNNY,tooltip="Brightness")
        self.contrast_icon = ft.Icon(name=ft.icons.CONTRAST,tooltip="Contrast")
        self.diameter_text = ft.Text("125.0", size=14, weight=ft.FontWeight.BOLD)
        self.diameter_display = ft.Container(
            content=ft.Row([ft.Icon(name=ft.icons.STRAIGHTEN_ROUNDED, tooltip="Average diameter"), self.diameter_text]),
            border_radius=12,
            padding=10,
            visible=False
        )


    def build(self):
        """
        Build up the main page of the GUI
        """
        self.page.add(
            ft.Column(
                [
                    ft.Row(
                        [
                            #LEFT COLUMN that handles all elements on the left side(canvas,switch_mask,segmentation)
                            ft.Column(
                                [
                                    self.canvas.canvas_card,
                                    ft.Row([self.switch_mask, self.drawing_button]),
                                    ft.Row([self.gui_config,ft.Column([ft.Card(content=ft.Container(content=ft.Column([ft.Row([self.brightness_icon,ft.Container(self.brightness_slider,padding=-15)]),ft.Row([self.contrast_icon,ft.Container(self.contrast_slider,padding=-15)])]),padding=10)),
                                                                       ft.Row([ft.Card(content=self.auto_brightness_contrast), ft.Card(content=self.diameter_display)])])
                                            ]),
                                    self.segmentation_card
                                ],
                                expand=True,
                                alignment=ft.MainAxisAlignment.START,
                            ),
                            #RIGHT COLUMN that handles gallery and directory_card
                            ft.Column(
                                [
                                    self.directory,
                                    ft.Card(
                                        content=ft.Container(self.directory.image_gallery,padding=20),
                                        expand=True
                                    ),
                                ],
                                expand=True,
                            ), self.op,
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        expand=True,
                    ),
                ],
                expand=True
            )
        )

        def update_view_mask(e):
            """
            Method that controls what happened when switch is on/off
            """
            if self.csp.image_id is None:
                print("No image selected")
                error_banner(self,"No image selected!")
                self.switch_mask.value=False
            else:
                handle_image_switch_mask_on(self)

        self.switch_mask.on_change = update_view_mask


    def start_drawing_window(self):
        multiprocessing.Process(target=open_qt_window, args=(self.queue,)).start()

    def set_queue_drawing_window(self):
        self.image_tuning.save_current_main_image()
        self.queue.put((self.csp.config.get_mask_color(),self.csp.config.get_outline_color(),self.csp.config.get_bf_channel(),self.csp.mask_paths,self.csp.image_id,self.csp.adjusted_image_path))

