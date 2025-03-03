import asyncio

import flet as ft
from cellsepi.frontend.main_window.gui_mask import handle_image_switch_mask_on

def update_main_image(img_id,channel_id,gui,on_click = True):
    """
    Method that handles what happens when the image is clicked or the main image need an update.
    """
    if on_click:
        if gui.csp.image_id is not None and gui.csp.image_id in gui.directory.selected_images_visualise:
            if gui.csp.channel_id is not None and gui.csp.channel_id in gui.directory.selected_images_visualise[gui.csp.image_id]:
                gui.directory.selected_images_visualise[gui.csp.image_id][gui.csp.channel_id].visible = False
                gui.directory.selected_images_visualise[gui.csp.image_id][gui.csp.channel_id].update()
    gui.csp.image_id = img_id
    gui.csp.channel_id = channel_id
    gui.directory.selected_images_visualise[img_id][channel_id].visible = True
    gui.directory.selected_images_visualise[img_id][channel_id].update()
    handle_image_switch_mask_on(gui)
    if on_click:
        gui.contrast_slider.value = 1.0
        gui.brightness_slider.value = 1.0
    gui.contrast_slider.update()
    gui.brightness_slider.update()
    if img_id is not None:
        gui.drawing_button.disabled = False
    else:
        gui.drawing_button.disabled = True
    gui.drawing_button.update()
    if not gui.auto_image_tuning.active:
        gui.contrast_slider.disabled = False
        gui.brightness_slider.disabled = False
        gui.page.update()
        asyncio.run(gui.image_tuning.update_brightness_and_contrast_async(on_click=on_click, linux=gui.csp.linux))
    else:
        gui.auto_image_tuning.update_main_image_auto()



class Canvas:
    """
    Creates the main_card with the main_image and mask.
    """
    def __init__(self):
        self.container_mask=ft.Container(ft.Image(src=r"data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA\AAAFCAIAAAFe0wxPAAAAAElFTkSuQmCC",fit=ft.ImageFit.SCALE_DOWN,),visible=False,alignment=ft.alignment.center)

        self.main_image = ft.Container(ft.Image(src=r"data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA\AAAFCAIAAAFe0wxPAAAAAElFTkSuQmCC",
                                    fit=ft.ImageFit.SCALE_DOWN),alignment=ft.alignment.center)

        self.canvas_card = self.create_canvas_card()
    def create_canvas_card(self):
        return ft.Card(
            content=ft.Stack([self.main_image, self.container_mask]),
            expand=True
        )

