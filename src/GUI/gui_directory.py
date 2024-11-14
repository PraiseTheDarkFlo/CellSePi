import os

import flet as ft
from . import GUI
from .gui_canvas import on_image_click

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
    gui.count_results_txt.value = f"Results: {len(gui.image_gallery.controls)}"
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
        if e.path:
            gui.directory_path.value = e.path
            load_images_from_directory(e.path)
        else:
            gui.image_gallery.controls.clear()
            gui.image_gallery.update()
        gui.formatted_path.value = format_directory_path(gui.directory_path)
        gui.formatted_path.update()

    #handels the files picking result
    def pick_files_result(e: ft.FilePickerResultEvent):
        # TODO
        gui.directory_path.value = "in development"
        gui.formatted_path.value = format_directory_path(gui.directory_path)
        gui.formatted_path.update()



    def load_images_from_directory(path):
        image_files = [f for f in os.listdir(path) if
                       f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.lif', '.tif'))]
        images = [os.path.join(path, f) for f in image_files]
        load_images(images)

    #load images to gallery in order and with names
    def load_images(images):
            gui.image_gallery.controls.clear()
            for img_path in images:
                file_name = os.path.basename(img_path)
                file_name = file_name.split('.')[0]
                current_image = ft.Image(src=img_path, height=200, width=200, fit=ft.ImageFit.COVER)
                current_image_container = ft.GestureDetector(
                    content=current_image,
                    on_tap=lambda e, path=img_path,g=gui: on_image_click(e, path,gui)
                )
                img_container = ft.Column(
                    [
                        ft.Text(file_name, weight="bold"),  # Name über dem Bild
                        current_image_container,
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=5  # Abstand zwischen Text und Bild
                )
                gui.image_gallery.controls.append(img_container)
            gui.image_gallery.update()
            update_results_text(gui)


    #create the rows for directory/file picking
    directory_row = ft.Row(
        [
            ft.ElevatedButton(
                "Open Directory",
                icon=ft.icons.FOLDER_OPEN,
                on_click=lambda _: get_directory_dialog.get_directory_path(),
                disabled=gui.page.web,
            ),
        ], alignment=ft.MainAxisAlignment.END
    )
    files_row = ft.Row(
        [
            ft.ElevatedButton(
                "Pick Files",
                icon=ft.icons.UPLOAD_FILE,
                on_click=lambda _: pick_files_dialog.pick_files(allow_multiple=False),
            )
        ], alignment=ft.MainAxisAlignment.END
    )
    #create the handlers
    get_directory_dialog = ft.FilePicker(on_result=get_directory_result)
    pick_files_dialog = ft.FilePicker(on_result=pick_files_result)
    #add the handlers to the page
    gui.page.overlay.extend([pick_files_dialog, get_directory_dialog])

    #changes the visibility of the directory/file picking
    def update_view(e):
        if gui.is_lif.value:
            files_row.visible = True
            directory_row.visible = False
        else:
            files_row.visible = False
            directory_row.visible = True
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
                                ), ft.Row([gui.is_lif,
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
                        ),
                        expand=True,
                    )
                ]

            ),
            width=gui.page.width * (1 / 3),
            padding=10,
            expand=True
        )
    )

