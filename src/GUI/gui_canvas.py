import flet as ft
import flet.canvas as fc
from . import GUI
from ..mask import Mask

#method that handles what happens when the image is clicked
def on_image_click(event, img_path,img_id,gui: GUI):
    print("selected img:",img_id)
    gui.csp.image_id = img_id
    gui.canvas.main_image.content = ft.Image(src=img_path, fit=ft.ImageFit.SCALE_DOWN)
    gui.page.update()


#class that handles the states of the canvas
class State:
    x: float
    y: float

#includes every thing about the canvas like drawing,the states, ...
class Canvas:
    def __init__(self):
        self.state = State()
        self.canvas = fc.Canvas(
            content=ft.GestureDetector(
                on_pan_start=self.pan_start,
                on_pan_update=self.pan_update,
                drag_interval=10,
            ),
        )

        self.container_canvas= ft.Container(self.canvas,border_radius=5)
        self.container_mask=ft.Container(ft.Image(src="image_xy01c1_seg.png",fit=ft.ImageFit.SCALE_DOWN,),visible=False,alignment=ft.alignment.center)

        self.main_image = ft.Container(ft.Image(src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA\AAAFCAIAAAFe0wxPAAAAAElFTkSuQmCC",
                                    fit=ft.ImageFit.SCALE_DOWN),alignment=ft.alignment.center)
        self.canvas_card = self.create_canvas_card()

    def create_canvas_card(self):
        return ft.Card(
            content=ft.Stack([self.main_image,self.container_mask ,self.container_canvas ]),
            width=700,
            height=500,
            expand=True,
            aspect_ratio=2
        )

    def pan_start(self,e: ft.DragStartEvent):
        self.state.x = e.local_x
        self.state.y = e.local_y

    def pan_update(self,e: ft.DragUpdateEvent):
        self.canvas.shapes.append(
            fc.Line(
                self.state.x, self.state.y, e.local_x, e.local_y, paint=ft.Paint(stroke_width=3)
            )
        )
        self.canvas.update()
        self.state.x = e.local_x
        self.state.y = e.local_y


