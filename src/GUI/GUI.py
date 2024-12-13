import asyncio
import multiprocessing

import flet as ft
from . import gui_options as op
from .gui_segmentation import create_segmentation_card
from .drawing.gui_drawing import open_qt_window
from .gui_canvas import Canvas
from .gui_config import GUIConfig
from .gui_directory import format_directory_path, copy_directory_to_clipboard, create_directory_card
from src.CellSePi import CellSePi
from src.mask import Mask
from .gui_mask import error_banner,handle_image_switch_mask_on
from ..image_tuning import ImageTuning


#class GUI to handle the complete GUI and their attributes, also contains the CellSePi class and updates their attributes
class GUI:
    def __init__(self,page: ft.Page):
        self.csp: CellSePi = CellSePi()
        self.page = page
        self.directory_path = ft.Text(weight="bold",value='Directory Path')
        self.image_gallery = ft.ListView()
        self.count_results_txt = ft.Text(value="Results: 0")
        self.lif_txt = ft.Text("Lif",weight="bold")
        self.tif_txt = ft.Text("Tif")
        self.is_lif = ft.CupertinoSwitch(value=True, active_color=ft.Colors.BLUE_ACCENT,track_color=ft.Colors.BLUE_ACCENT)
        self.switch_mask = ft.Switch(label="Mask", value=False)
        self.drawing_button= ft.ElevatedButton(text="Drawing Tools", icon="brush_rounded",on_click=lambda e: self.start_drawing_window())
        self.page.window.width = 1400
        self.page.window.height = 825
        self.page.window_left = 200
        self.page.window_top = 50
        self.page.window.min_width = self.page.window.width
        self.page.window.min_height = self.page.window.height
        self.page.title = "CellSePi"
        self.formatted_path = ft.Text(format_directory_path(self.directory_path), weight="bold")
        self.canvas = Canvas()
        self.directory_card = create_directory_card(self)
        gui_config = GUIConfig(self)
        self.gui_config = gui_config.create_profile_container()
        seg_card,start_button,open_button,progress_bar,progress_bar_text = create_segmentation_card(self)
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

        # Slider für Kontrast
        self.contrast_slider = ft.Slider(
            min=0, max=2.0, value=1.0, disabled= True,
            on_change=lambda e: asyncio.run(self.image_tuning.update_main_image_async())
        )

    def build(self): #build up the main page of the GUI
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
                                    ft.Row([self.gui_config,ft.Card(content=ft.Container(content=ft.Column([ft.Row([ft.Icon(name=ft.icons.SUNNY,tooltip="Brightness"),ft.Container(self.brightness_slider,padding=-15)]),ft.Row([ft.Icon(name=ft.icons.CONTRAST,tooltip="Contrast"),ft.Container(self.contrast_slider,padding=-15)])]),padding=10))]),
                                    self.segmentation_card
                                ],
                                expand=True,
                                alignment=ft.MainAxisAlignment.START,
                            ),
                            #RIGHT COLUMN that handles gallery and directory_card
                            ft.Column(
                                [
                                    self.directory_card,
                                    ft.Card(
                                        content=ft.Container(self.image_gallery,padding=20),
                                        expand=True
                                    ),
                                ],
                                expand=True,
                            ), op.switch(self.page)
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        expand=True,
                    ),
                ],
                expand=True
            )
        )
        #method that controls what happened when switch is on/off
        def update_view_mask(e):

            if self.csp.image_id is None:
                print("No image selected")
                error_banner(self,"No image selected!")
                self.switch_mask.value=False
            else:
                handle_image_switch_mask_on(self)

        self.switch_mask.on_change = update_view_mask


    def start_drawing_window(self):
        self.image_tuning.save_current_main_image()
        multiprocessing.Process(target=open_qt_window, args=(self.csp,)).start()

