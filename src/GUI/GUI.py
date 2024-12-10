import asyncio
import base64
import multiprocessing
import os
import sys
import threading
from io import BytesIO

from PIL import Image, ImageEnhance
import flet as ft
from PyQt5.QtWidgets import QApplication
from scipy.constants import value

from . import gui_options as op, gui_segmentation
from .drawing.gui_drawing import open_qt_window
from .gui_canvas import Canvas
from .gui_config import GUIConfig
from .gui_directory import format_directory_path, copy_directory_to_clipboard, create_directory_card
from src.CellSePi import CellSePi
from src.mask import Mask


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
        self.directory_card = create_directory_card(self)
        self.canvas = Canvas()
        gui_config = GUIConfig(self)
        self.gui_config = gui_config.create_profile_container()
        self.segmentation_card = gui_segmentation.create_segmentation_card(self)
        self.mask=Mask(self.csp)
        self.brightness_slider = ft.Slider(
            min=0, max=2.0, value=1.0, label="Helligkeit {value}",
            on_change=lambda e: asyncio.run(self.update_main_image_async())
        )

        # Slider für Kontrast
        self.contrast_slider = ft.Slider(
            min=0, max=2.0, value=1.0, label="Kontrast {value}",
            on_change=lambda e: asyncio.run(self.update_main_image_async())
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
                                    self.canvas.canvas_card
                                    ,
                                    ft.Row([self.switch_mask,self.drawing_button,self.brightness_slider,self.contrast_slider]),
                                    self.gui_config,
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
            if self.switch_mask.value:
                print("on")
                #if self.mask.output_saved:
                path =self.mask.load_mask_into_canvas()
                print("in gui i selected:",self.csp.image_id)
                image=self.csp.image_id
                mask=self.mask.mask_outputs[image]
                print(mask)
                self.canvas.container_mask.image_src= mask
                self.canvas.container_mask.visible=True
                #TODO: hier wenn ein click event, dann soll sich die Maske ausschalten
                #else:
                    #add page error message
                 #   print("There is no mask to display")

            else:
                print("off")
                self.canvas.container_mask.visible=False

            self.page.update()
        self.switch_mask.on_change = update_view_mask

    async def update_main_image_async(self):
        base64_image = await self.adjust_image_async(
            round(self.brightness_slider.value, 2),
            round(self.contrast_slider.value, 2)
        )
        self.canvas.main_image.content.src_base64 = base64_image
        self.canvas.main_image.update()

    async def adjust_image_async(self, brightness, contrast):
        return await asyncio.to_thread(self.adjust_image_in_memory, brightness, contrast)

    def adjust_image_in_memory(self, brightness, contrast):
        image_path = self.csp.image_paths[self.csp.image_id][self.csp.channel_id]
        image = self.load_image(image_path)

        enhancer = ImageEnhance.Brightness(image)
        image = enhancer.enhance(brightness)

        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(contrast)

        buffer = BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)

        return base64.b64encode(buffer.getvalue()).decode('utf-8')

    def load_image(self, image_path):
        if self.csp.cached_image and self.csp.cached_image[0] == image_path:
            return self.csp.cached_image[1]

        image = Image.open(image_path)
        self.csp.cached_image = (image_path, image)
        return image

    def save_current_main_image(self):
        image_data = base64.b64decode(self.canvas.main_image.content.src_base64)
        buffer = BytesIO(image_data)
        if self.csp.adjusted_image_path is None:
            self.csp.adjusted_image_path = os.path.join(self.csp.working_directory, "adjusted_image.png")
        image = Image.open(buffer)
        image.save(self.csp.adjusted_image_path, format="PNG")

    def start_drawing_window(self):
        self.save_current_main_image()
        multiprocessing.Process(target=open_qt_window, args=(self.csp,)).start()