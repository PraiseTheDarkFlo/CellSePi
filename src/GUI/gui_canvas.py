import flet as ft
import flet.canvas as fc
from . import GUI
from ..mask import Mask

#method that handles what happens when the image is clicked
def on_image_click(event,img_id,channel_id,gui: GUI):
    print("selected img:",img_id)
    gui.csp.image_id = img_id
    gui.csp.channel_id = channel_id
    gui.update_main_image()


#includes every thing about the canvas like drawing,the states, ...
class Canvas:
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

