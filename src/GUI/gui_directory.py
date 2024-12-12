import os
import pathlib

import flet as ft
from PIL import Image

from . import GUI
from .gui_canvas import on_image_click
from .gui_mask import handle_image_switch_mask_on
from ..data_util import extract_from_lif_file, copy_files_between_directories, load_directory,transform_image_path


#format the directory so that it can be shown in the card
def format_directory_path(dir_path, max_length=30):
    parts = dir_path.value.split('/')
    path = dir_path.value
    if len(dir_path.value) > max_length:
        if len(parts) > 2:
            path = f".../{parts[len(parts) - 2]}/{parts[len(parts) - 1]}"
        else:
            return f"...{path[len(parts) - (max_length - 3):]}"

    if len(path) > max_length:
        path = f"...{path[len(parts) - (max_length - 3):]}"  # 3 für '...'

    return path

def update_results_text(gui: GUI):
    gui.count_results_txt.value = f"Results: {len(gui.csp.image_paths)}"
    gui.count_results_txt.update()

#adds the directory in to the clipboard and opens the snack_bar and say that it has been copied
def copy_directory_to_clipboard(e,gui: GUI):
    gui.page.set_clipboard(gui.directory_path.value)
    gui.page.snack_bar = ft.SnackBar(ft.Text("Directory path copied to clipboard!"))
    gui.page.snack_bar.open = True
    gui.page.update()

#creates the directory card with all event handlers
def create_directory_card(gui: GUI):
    #handels the directory picking result
    def get_directory_result(e: ft.FilePickerResultEvent):
        if not(e.files is None and e.path is None):
            if gui.is_lif.value:
                path = e.files[0].path
            else:
                path = e.path
            if path:
                gui.directory_path.value = path
                select_directory(path)
                load_images()
            else:
                gui.image_gallery.controls.clear()
                gui.image_gallery.update()

            gui.formatted_path.value = format_directory_path(gui.directory_path)
            gui.formatted_path.update()
            gui.contrast_slider.disabled = True
            gui.brightness_slider.disabled = True
            gui.contrast_slider.update()
            gui.brightness_slider.update()

    def select_directory(dir):
        is_lif = gui.is_lif.value
        # print("Remove fixed dir")
        # dirname = "/Users/erik/Documents/Promotion/Projekte/Anjas_Stuff/Cellpose Train/"
        print(dir)
        path = pathlib.Path(dir)
        # Lif Case
        if is_lif:
            working_directory = path.parent / "output/"
            os.makedirs(working_directory, exist_ok=True)
            if path.suffix.lower() == ".lif":
                # Extract from lif file all the single series images and extract to .tif, .tiff and .npy files into subdirectory
                extract_from_lif_file(lif_path=path, target_dir=working_directory)
            pass


        # Tiff Case
        else:
            # Copy .tif, .tiff and .npy files into subdirectory
            working_directory = path / "output/"
            os.makedirs(working_directory, exist_ok=True)
            copy_files_between_directories(path, working_directory, file_types=[".tif", ".tiff", ".npy"])
            for path in working_directory.iterdir():
                if path.suffix.lower() == ".tif" or path.suffix.lower() == ".tiff":
                    if path.is_file():
                        transform_image_path(path, path, gui)
                    if Image.open(path).mode in ["L", "RGB"]:
                        print("8 bit")


        gui.csp.working_directory = working_directory
        set_paths(working_directory)


    def set_paths(dirname):
        bfc = gui.csp.config.get_bf_channel()
        cp = gui.csp.config.get_channel_prefix()
        ms = gui.csp.config.get_mask_suffix()

        image_paths, mask_paths = load_directory(dirname, bright_field_channel=bfc, channel_prefix=cp, mask_suffix=ms)
        if len(image_paths) == 0:
            gui.page.snack_bar = ft.SnackBar(ft.Text("The directory contains no valid files with the current Channel Prefix!"))
            gui.page.snack_bar.open = True
            gui.page.update()
            gui.count_results_txt.color = ft.Colors.RED
            os.rmdir(gui.csp.working_directory)
        else:
            gui.count_results_txt.color = None

        gui.csp.image_paths = image_paths
        gui.csp.mask_paths = mask_paths
        print(f"Selected Directory: {dirname}")
        print(f"This directory contains {len(image_paths)} unique image ids.")

        print(f"This directory contains {len(mask_paths)} unique mask ids.")


    #load images to gallery in order and with names
    def load_images():
        gui.image_gallery.controls.clear()
        gui.canvas.main_image.content = ft.Image(src=r"data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA\AAAFCAIAAAFe0wxPAAAAAElFTkSuQmCC",
                                    fit=ft.ImageFit.SCALE_DOWN)
        gui.canvas.main_image.update()

        # Display groups with side-by-side images
        for image_id in gui.csp.image_paths:
            cur_image_paths = gui.csp.image_paths[image_id]
            group_row = ft.Row(
                [
                    ft.Column(
                        [
                            ft.GestureDetector(
                                content=ft.Image(
                                    src=cur_image_paths[img_path],
                                    height=150,
                                    width=150,
                                    fit=ft.ImageFit.CONTAIN
                                ),
                                on_tap=lambda e,img_id = image_id,channel_id = img_path, g=gui: on_image_click(e,img_id,channel_id, g)
                            ),
                            ft.Text(img_path, size=10, text_align="center"),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=5
                    )
                    for img_path in cur_image_paths
                ],
                alignment=ft.MainAxisAlignment.START,
                spacing=10,
                scroll=ft.ScrollMode.AUTO,
            )
            gui.image_gallery.controls.append(
                ft.Column(
                    [
                        ft.Text(f"{image_id}", weight="bold",text_align=ft.TextAlign.CENTER),
                        group_row
                    ],
                    spacing=10,
                    alignment = ft.MainAxisAlignment.CENTER
                )
            )

        gui.image_gallery.update()
        update_results_text(gui)


    #create the rows for directory/file picking
    home_dir = os.path.expanduser("~")
    directory_row = ft.Row(
        [
            ft.ElevatedButton(
                "Open Directory",
                icon=ft.icons.FOLDER_OPEN,
                on_click=lambda _: get_directory_dialog.get_directory_path(),
                disabled=gui.page.web,
            ),
        ], alignment=ft.MainAxisAlignment.START  # Change alignment to extend fully to the left
    )
    files_row = ft.Row(
        [
            ft.ElevatedButton(
                "Pick File",
                icon=ft.icons.UPLOAD_FILE,
                on_click=lambda _: pick_files_dialog.pick_files(allow_multiple=False),
            )
        ], alignment=ft.MainAxisAlignment.START  # Change alignment to extend fully to the left
    )
    #create the handlers
    get_directory_dialog = ft.FilePicker(on_result=get_directory_result)
    pick_files_dialog = ft.FilePicker(on_result=get_directory_result)
    #add the handlers to the page
    gui.page.overlay.extend([pick_files_dialog, get_directory_dialog])

    #changes the visibility of the directory/file picking
    def update_view(e):
        if gui.is_lif.value:
            gui.lif_txt.weight = "bold"
            gui.tif_txt.weight = "normal"
            files_row.visible = True
            directory_row.visible = False

        else:
            gui.lif_txt.weight = "normal"
            gui.tif_txt.weight = "bold"
            files_row.visible = False
            directory_row.visible = True

        gui.switch_mask.value = False
        gui.canvas.container_mask.visible = False
        gui.csp.image_id = None
        gui.canvas.main_image.content= ft.Image(src=r"data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA\AAAFCAIAAAFe0wxPAAAAAElFTkSuQmCC",
                                    fit=ft.ImageFit.SCALE_DOWN)
        gui.page.update()


    update_view(None)
    gui.is_lif.on_change = update_view

    #creates the directory_card and returns it
    return ft.Card(
        content=ft.Container(
            content=ft.Stack(
                [
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.ListTile(
                                    leading=ft.Icon(name=ft.icons.FOLDER_OPEN),
                                    title=gui.formatted_path,
                                    subtitle=gui.count_results_txt
                                ), ft.Row([ft.Container(content=ft.Row([gui.tif_txt,gui.is_lif,gui.lif_txt],spacing=0)),
                                           directory_row,
                                           files_row, ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                                          )
                            ]
                        )
                    ),
                    ft.Container(
                        content=ft.Container(
                            content=ft.IconButton(
                                icon=ft.icons.COPY,
                                tooltip="Copy to clipboard",
                                on_click=lambda e,g=gui: copy_directory_to_clipboard(e,gui)
                            ),
                            alignment=ft.alignment.top_right,
                        )
                    )
                ]

            ),
            padding=10,
        )
    )
