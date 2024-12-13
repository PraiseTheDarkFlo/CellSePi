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
#TODO: verhindern, dass die Maske noch sichtbar ist, wenn das Bild gewechselt wird, aber die Maske nicht geladen wird
    if gui.switch_mask.value:
        print("on")
        image = gui.csp.image_id
        bfc=gui.csp.config.get_bf_channel()

        #case: mask was created during segmentation
        if image in gui.csp.mask_paths and bfc in gui.csp.mask_paths[image]:
            #if the image to the bright-field channel was not generated before
            if image not in gui.mask.mask_outputs or bfc not in gui.mask.mask_outputs[image]:
                gui.mask.load_mask_into_canvas()

            #loads mask into container
            mask = gui.mask.mask_outputs[image][bfc]
            print(mask)
            gui.canvas.container_mask.image_src = mask
            gui.canvas.container_mask.visible = True
        else:#hier prüfeb, ob Bildpfad im Canvas derselbe Pfad ist wie der ausgewählte
            error_banner(gui,f"There is no mask for {gui.csp.image_id} with bright-field channel {bfc} generated ")
            gui.canvas.container_mask.visible = False
            gui.switch_mask.value=False
    else:
        print("off")
        gui.canvas.container_mask.visible = False

    gui.page.update()