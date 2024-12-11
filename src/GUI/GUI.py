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
from .gui_mask import error_banner,handle_image_switch_mask_on

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
            min=0, max=2.0, value=1.0, disabled= True,
            on_change=lambda e: asyncio.run(self.update_main_image_async())
        )

        # Slider für Kontrast
        self.contrast_slider = ft.Slider(
            min=0, max=2.0, value=1.0, disabled= True,
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
                error_banner(self)
            else:
                handle_image_switch_mask_on(self)

        self.switch_mask.on_change = update_view_mask

    import asyncio

    async def update_main_image_async(self,click= False):
        if  click:
            self.cancel_all_tasks()
            self.canvas.main_image.content.src_base64 = None
            self.canvas.main_image.content.src = self.csp.image_paths[self.csp.image_id][self.csp.channel_id]
            self.canvas.main_image.update()
        else:
            task = asyncio.create_task(self.update_image())
            self.canvas.running_tasks.add(task)
            try:
                await task
            except asyncio.CancelledError:
                pass
            finally:
                self.canvas.running_tasks.discard(task)

    def cancel_all_tasks(self):
        for task in self.canvas.running_tasks:
            print("canceled")
            task.cancel()
        self.canvas.running_tasks.clear()

    async def update_image(self):
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
        if self.csp.adjusted_image_path is None:
            self.csp.adjusted_image_path = os.path.join(self.csp.working_directory, "adjusted_image.png")
        if round(self.brightness_slider.value, 2) == 1 and round(self.contrast_slider.value, 2) == 1:
            image = self.load_image(self.csp.image_paths[self.csp.image_id][self.csp.channel_id])
            image.save(self.csp.adjusted_image_path, format="PNG")
        else:
            image_data = base64.b64decode(self.canvas.main_image.content.src_base64)
            buffer = BytesIO(image_data)
            image = Image.open(buffer)
            image.save(self.csp.adjusted_image_path, format="PNG")

    def start_drawing_window(self):
        self.save_current_main_image()
        multiprocessing.Process(target=open_qt_window, args=(self.csp,)).start()

