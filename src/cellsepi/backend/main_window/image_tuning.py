import asyncio
import base64
import os
from io import BytesIO
import flet as ft
import cv2
from PIL import Image, ImageEnhance
from matplotlib import pyplot as plt
from cellsepi.frontend.main_window.gui_canvas import update_main_image


class ImageTuning:
    """
    Manages the task to tune the image brightness and contrast.
    Attributes:
        gui (GUI): The GUI object that contains all objects for the gui.
        running_tasks: contains all task that are currently running.
        cached_image: contains the image that is current be cached.
    """
    def __init__(self,gui):
        self.gui = gui
        self.running_tasks = set()
        self.cached_image = None
    async def update_brightness_and_contrast_async(self, on_click=False,linux = False):
        """
        Updates the main image brightness and contrast with the current selected values with the sliders.

        If a new image was clicked all old tasked got cancel so the new image has prio over the old one.

        Args:
            on_click (bool): if a new main image is clicked or not.
            linux (bool): if the program is running on Linux.
        """
        if linux and on_click:
            self.cancel_all_tasks()
            self.gui.canvas.main_image.content.src_base64 = self.gui.csp.linux_images[self.gui.csp.image_id][self.gui.csp.channel_id]
            self.gui.canvas.main_image.update()
        elif on_click:
            self.cancel_all_tasks()
            self.gui.canvas.main_image.content.src_base64 = None
            self.gui.canvas.main_image.content.src = self.gui.csp.image_paths[self.gui.csp.image_id][self.gui.csp.channel_id]
            self.gui.canvas.main_image.update()
        else:
            task = asyncio.create_task(self.update_image())
            self.running_tasks.add(task)
            try:
                await task
            except asyncio.CancelledError:
                pass
            finally:
                self.running_tasks.discard(task)

    def cancel_all_tasks(self):
        for task in self.running_tasks:
            task.cancel()
        self.running_tasks.clear()


    async def update_image(self):
        """
        Updates the main image as base64_image with the new brightness and contrast values.
        """
        base64_image = await self.adjust_image_async(
            round(self.gui.brightness_slider.value, 2),
            round(self.gui.contrast_slider.value, 2)
        )
        self.gui.canvas.main_image.content.src_base64 = base64_image
        self.gui.canvas.main_image.update()

    async def adjust_image_async(self, brightness, contrast):
        return await asyncio.to_thread(self.adjust_image_in_memory, brightness, contrast)

    def adjust_image_in_memory(self, brightness, contrast):
        """
        Gets the current selected image and changes its brightness and contrast.
        Without saving it to disk.

        Args:
            brightness (int): the selected image's brightness'.
            contrast (int): the selected image's contrast'.

        Returns:
            image (base64): the updated image.
        """
        image_path = self.gui.csp.image_paths[self.gui.csp.image_id][self.gui.csp.channel_id]
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
        """
        Checks if the image is already loaded.
        If not, it gets the new one from the image_path

        Args:
            image_path (str): the path to the image

        Returns:
            image (pillow): the loaded image.
        """
        if self.cached_image and self.cached_image[0] == image_path:
            return self.cached_image[1]

        image = Image.open(image_path)
        self.cached_image = (image_path, image)
        return image

    def save_current_main_image(self):
        """
        Saves the current selected image to disk.
        """
        if self.gui.csp.adjusted_image_path is None:
            self.gui.csp.adjusted_image_path = os.path.join(self.gui.csp.working_directory, "adjusted_image.png")
        if round(self.gui.brightness_slider.value, 2) == 1 and round(self.gui.contrast_slider.value, 2) == 1 and not self.gui.auto_image_tuning.active:
            image = self.load_image(self.gui.csp.image_paths[self.gui.csp.image_id][self.gui.csp.channel_id])
            image.save(self.gui.csp.adjusted_image_path, format="PNG")
        else:
            image_data = base64.b64decode(self.gui.canvas.main_image.content.src_base64)
            buffer = BytesIO(image_data)
            image = Image.open(buffer)
            image.save(self.gui.csp.adjusted_image_path, format="PNG")

class AutoImageTuning:
    def __init__(self, gui):
        self.gui = gui
        self.active = False

    def pressed(self):
        if self.active:
            self.active = False
            self.gui.csp.config.set_auto_button(False)
            self.gui.auto_brightness_contrast.icon_color = ft.Colors.GREY_700
            if self.gui.csp.image_id is not None:
                self.gui.brightness_slider.disabled = False
                self.gui.contrast_slider.disabled = False
            self.gui.brightness_icon.color = None
            self.gui.contrast_icon.color = None
            self.gui.page.update()
            if self.gui.csp.image_id is not None:
                update_main_image(self.gui.csp.image_id, self.gui.csp.channel_id, self.gui, False)
        else:
            self.active = True
            self.gui.csp.config.set_auto_button(True)
            self.gui.auto_brightness_contrast.icon_color= ft.Colors.ORANGE_700
            if self.gui.csp.image_id is not None:
                self.gui.brightness_slider.disabled = True
                self.gui.contrast_slider.disabled = True
            self.gui.brightness_icon.color = ft.Colors.GREY_700
            self.gui.contrast_icon.color = ft.Colors.GREY_700
            self.gui.page.update()
            if self.gui.csp.image_id is not None:
                update_main_image(self.gui.csp.image_id, self.gui.csp.channel_id, self.gui, False)

    def update_main_image_auto(self):
        self.gui.canvas.main_image.content.src_base64 = self.auto_adjust()
        self.gui.canvas.main_image.update()

    def auto_adjust(self):
        image_path = self.gui.csp.image_paths[self.gui.csp.image_id][self.gui.csp.channel_id]

        image = cv2.imread(image_path, cv2.IMREAD_COLOR)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        normalized_image = cv2.normalize(image, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX)

        _, buffer = cv2.imencode('.png', normalized_image)

        return base64.b64encode(buffer).decode('utf-8')

