import os
import flet as ft
from . import GUI


# Format the directory to display properly in the UI
def format_directory_path(dir_path, max_length=30):
    parts = dir_path.value.split('/')
    path = dir_path.value
    if len(dir_path.value) > max_length:
        if len(parts) > 2:
            path = f".../{parts[len(parts) - 2]}/{parts[len(parts) - 1]}"
        else:
            return f"...{path[len(parts) - (max_length - 3):]}"
    if len(path) > max_length:
        path = f"...{path[len(parts) - (max_length - 3):]}"  # 3 for '...'
    return path


def update_results_text(gui: GUI):
    gui.count_results_txt.value = f"Results: {len(gui.image_gallery.controls)}"
    gui.count_results_txt.update()


# Copy directory to clipboard and show a notification
def copy_directory_to_clipboard(e, gui: GUI):
    gui.page.set_clipboard(gui.directory_path.value)
    gui.page.snack_bar = ft.SnackBar(ft.Text("Directory path copied to clipboard!"))
    gui.page.snack_bar.open = True
    gui.page.update()


# Function to handle when an image is clicked
def on_image_click(e, img_path, gui):
    print(f"Image clicked: {img_path}")
    render_image_view(img_path, gui)


# Function to render a detailed view of the image
def render_image_view(img_path, gui, overlay_data=None):
    img = ft.Image(src=img_path, fit=ft.ImageFit.CONTAIN)

    # Add overlay if available (e.g., segmentation mask)
    if overlay_data:
        mask_overlay = ft.Container(
            content=ft.Image(src=overlay_data, fit=ft.ImageFit.CONTAIN, opacity=0.5),
            alignment=ft.alignment.center,
        )
        img = ft.Stack([img, mask_overlay])

    gui.detailed_view.content = img
    gui.detailed_view.update()


# Create the directory card with all its event handlers
def create_directory_card(gui: GUI):
    # Handles directory selection result
    def get_directory_result(e: ft.FilePickerResultEvent):
        if e.path:
            gui.directory_path.value = e.path
            load_images_from_directory(e.path)
        else:
            gui.image_gallery.controls.clear()
            gui.image_gallery.update()
        gui.formatted_path.value = format_directory_path(gui.directory_path)
        gui.formatted_path.update()

    # Handles file selection result
    def pick_files_result(e: ft.FilePickerResultEvent):
        gui.directory_path.value = "in development"
        gui.formatted_path.value = format_directory_path(gui.directory_path)
        gui.formatted_path.update()

    # Load images from the selected directory
    def load_images_from_directory(path):
        image_files = [f for f in os.listdir(path) if
                       f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.lif', '.tif'))]
        images = [os.path.join(path, f) for f in image_files]
        load_images(images)

    # Updated load_images function for side-by-side grouping
    def load_images(images):
        gui.image_gallery.controls.clear()

        # Group images by prefix
        grouped_images = {}
        for img_path in images:
            file_name = os.path.basename(img_path).split('.')[0]
            group_id = ''.join(filter(str.isalnum, file_name[:-2]))
            if group_id not in grouped_images:
                grouped_images[group_id] = []
            grouped_images[group_id].append((file_name, img_path))

        # Display groups with side-by-side images
        for group_id, image_data in grouped_images.items():
            group_row = ft.Row(
                [
                    ft.Column(
                        [
                            ft.GestureDetector(
                                content=ft.Image(
                                    src=img_path,
                                    height=150,
                                    width=150,
                                    fit=ft.ImageFit.CONTAIN
                                ),
                                on_tap=lambda e, path=img_path, g=gui: on_image_click(e, path, g)
                            ),
                            ft.Text(img_name, size=10, text_align="center"),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=5
                    )
                    for img_name, img_path in image_data
                ],
                alignment=ft.MainAxisAlignment.START,
                spacing=10
            )

            gui.image_gallery.controls.append(
                ft.Column(
                    [
                        ft.Text(f"Group: {group_id}", weight="bold"),
                        group_row
                    ],
                    spacing=10
                )
            )

        gui.image_gallery.update()
        update_results_text(gui)

    home_dir = os.path.expanduser("~")
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
                on_click=lambda _: pick_files_dialog.pick_files(allow_multiple=False, initial_directory=home_dir),
            )
        ], alignment=ft.MainAxisAlignment.END
    )

    get_directory_dialog = ft.FilePicker(on_result=get_directory_result)
    pick_files_dialog = ft.FilePicker(on_result=pick_files_result)
    gui.page.overlay.extend([pick_files_dialog, get_directory_dialog])

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
                                ),
                                ft.Row(
                                    [gui.is_lif, directory_row, files_row],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                                )
                            ]
                        )
                    ),
                    ft.Container(
                        content=ft.Container(
                            content=ft.IconButton(
                                icon=ft.icons.COPY,
                                tooltip="Copy to clipboard",
                                on_click=lambda e, g=gui: copy_directory_to_clipboard(e, g)
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
