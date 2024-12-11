from src import mask
from . import GUI
import flet as ft

def error_banner(gui:GUI):
    gui.page.snack_bar = ft.SnackBar(
        ft.Text("No image selected!"))
    gui.page.snack_bar.open = True
    gui.page.update()

def handle_image_switch_mask_on(gui:GUI):
    """
    loads the mask into the GUI if the switch is on
    Args:
        gui (GUI):the current GUI object

    """

    if gui.switch_mask.value:
        print("on")
        # if self.mask.output_saved:
        path = gui.mask.load_mask_into_canvas()
        print("in gui i selected:", gui.csp.image_id)
        image = gui.csp.image_id
        mask = gui.mask.mask_outputs[image]
        print(mask)
        gui.canvas.container_mask.image_src = mask
        gui.canvas.container_mask.visible = True

    else:
        print("off")
        gui.canvas.container_mask.visible = False

    gui.page.update()