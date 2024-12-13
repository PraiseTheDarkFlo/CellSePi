import asyncio
import base64
import os
from io import BytesIO

from PIL import Image, ImageEnhance
from src.GUI import GUI


class ImageTuning:
    def __init__(self,gui: GUI):
        self.gui = gui
        self.running_tasks = set()
    async def update_main_image_async(self, click=False):
        if click:
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
            print("canceled")
            task.cancel()
        self.running_tasks.clear()

    async def update_image(self):
        base64_image = await self.adjust_image_async(
            round(self.gui.brightness_slider.value, 2),
            round(self.gui.contrast_slider.value, 2)
        )
        self.gui.canvas.main_image.content.src_base64 = base64_image
        self.gui.canvas.main_image.update()

    async def adjust_image_async(self, brightness, contrast):
        return await asyncio.to_thread(self.adjust_image_in_memory, brightness, contrast)

    def adjust_image_in_memory(self, brightness, contrast):
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
        if self.gui.csp.cached_image and self.gui.csp.cached_image[0] == image_path:
            return self.gui.csp.cached_image[1]

        image = Image.open(image_path)
        self.gui.csp.cached_image = (image_path, image)
        return image

    def save_current_main_image(self):
        if self.gui.csp.adjusted_image_path is None:
            self.gui.csp.adjusted_image_path = os.path.join(self.gui.csp.working_directory, "adjusted_image.png")
        if round(self.gui.brightness_slider.value, 2) == 1 and round(self.gui.contrast_slider.value, 2) == 1:
            image = self.load_image(self.gui.csp.image_paths[self.gui.csp.image_id][self.gui.csp.channel_id])
            image.save(self.gui.csp.adjusted_image_path, format="PNG")
        else:
            image_data = base64.b64decode(self.gui.canvas.main_image.content.src_base64)
            buffer = BytesIO(image_data)
            image = Image.open(buffer)
            image.save(self.gui.csp.adjusted_image_path, format="PNG")
