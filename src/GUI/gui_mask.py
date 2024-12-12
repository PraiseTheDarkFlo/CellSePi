from src import mask
from . import GUI
import flet as ft

def error_banner(gui:GUI,message):
    gui.page.snack_bar = ft.SnackBar(
        ft.Text(message))
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
        image = gui.csp.image_id
        if image in gui.csp.mask_paths:
            #if the image was not generated before
            if image not in gui.mask.mask_outputs:
                gui.mask.load_mask_into_canvas()

            mask = gui.mask.mask_outputs[image]
            print(mask)
            gui.canvas.container_mask.image_src = mask
            gui.canvas.container_mask.visible = True
        else:
            error_banner(gui,f"There is no mask for {gui.csp.image_id} generated ")
            gui.switch_mask.value=False
    else:
        print("off")
        gui.canvas.container_mask.visible = False

    gui.page.update()