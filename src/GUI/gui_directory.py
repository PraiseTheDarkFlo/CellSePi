import os
import pathlib
import platform
from concurrent.futures import ThreadPoolExecutor
from json.encoder import INFINITY
from time import time
import flet as ft
from PIL import Image

from . import GUI
from .gui_canvas import on_image_click
from .gui_fluorescence import fluorescence_button
from ..avg_diameter import AverageDiameter
from ..data_util import extract_from_lif_file, copy_files_between_directories, load_directory, transform_image_path, \
    convert_tiffs_to_png_parallel


def format_directory_path(dir_path, max_length=30):
    """
    Format the directory so that it can be shown in the card.
    Args:
        dir_path (Txt): Path to the directory that should be formatted.
        max_length (int): Maximum length of the directory path.
    """
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

def copy_directory_to_clipboard(e,gui: GUI):
    """
    Adds the directory in to the clipboard and opens the snack_bar and say that it has been copied.
    """
    gui.page.set_clipboard(gui.directory.directory_path.value)
    gui.page.snack_bar = ft.SnackBar(ft.Text("Directory path copied to clipboard!"))
    gui.page.snack_bar.open = True
    gui.page.update()


def get_Image(linux: bool, src):
    """
    Adjust the method of reading the image, depending on whether the system is Linux or not (src_Base64 or src).
    Args:
        linux (bool): Whether the system is Linux or not.
        src (str): The path of the image to load.
    Returns:
          ft.Image: the image at the src path.
    """
    if linux:
        return ft.Image(
            src_base64=src,
            height=150,
            width=150,
            fit=ft.ImageFit.CONTAIN
        )
    else:
        return ft.Image(
            src=src,
            height=150,
            width=150,
            fit=ft.ImageFit.CONTAIN
        )


class DirectoryCard(ft.Card):
    """
    Handles the directory card with all event handlers.
    """
    def __init__(self, gui: GUI):
        super().__init__()
        self.gui = gui
        self.count_results_txt = ft.Text(value="Results: 0")
        self.directory_path = ft.Text(weight="bold",value='Directory Path')
        self.formatted_path = ft.Text(format_directory_path(self.directory_path), weight="bold")
        self.is_lif = True
        self.lif_slider = ft.CupertinoSlidingSegmentedButton(
            selected_index=1,
            thumb_color=ft.Colors.BLUE_400,
            on_change=self.update_view,
            padding=ft.padding.symmetric(0, 0),
            controls=[
                ft.Text("Tif"),
                ft.Text("Lif")
            ],
        )
        self.image_gallery = ft.ListView()
        self.path_list_tile = self.create_path_list_tile()
        self.get_directory_dialog = None
        self.pick_files_dialog = None
        self.create_handlers()
        self.directory_row = self.create_dir_row()
        self.files_row = self.create_files_row()
        self.lif_slider_blocker = ft.Container(
            width=80,
            height=30,
            bgcolor=ft.Colors.TRANSPARENT,
            on_click= None,
            visible= False,
        )
        self.lif_row = ft.Row([ft.Stack([self.lif_slider,self.lif_slider_blocker]),
                                               self.directory_row,
                                               self.files_row
                                                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                                              )
        self.content = self.create_directory_container()
        self.output_dir = False
        self.files_row.visible = True
        self.directory_row.visible = False

    def create_path_list_tile(self):
        return ft.ListTile(leading=ft.Icon(name=ft.icons.FOLDER_OPEN),
                    title=self.formatted_path,
                    subtitle=self.count_results_txt
                    )

    def update_results_text(self):
        self.count_results_txt.value = f"Results: {len(self.gui.csp.image_paths)}"
        self.count_results_txt.update()

    def get_directory_result(self, e: ft.FilePickerResultEvent):
        """
        Checks if the picked directory or file exists and if it worked updates every thing with the new values.
        """
        if not(e.files is None and e.path is None):
            if self.is_lif:
                path = e.files[0].path
            else:
                path = e.path
            if path:
                self.directory_path.value = path
                self.select_directory_parallel(path)
                #self.benchmark_seq_and_par(path)
                self.load_images()
            else:
                self.image_gallery.controls.clear()
                self.image_gallery.update()

            self.formatted_path.value = format_directory_path(self.directory_path)
            if self.output_dir:
                self.formatted_path.color = ft.Colors.RED
            else:
                self.formatted_path.color = None
            self.formatted_path.update()
            self.gui.contrast_slider.disabled = True
            self.gui.brightness_slider.disabled = True
            self.gui.contrast_slider.update()
            self.gui.brightness_slider.update()

    def select_directory(self,directory_path):
        """
        Gets the working directory and copies the images in there.

        Args:
            directory_path (str): the selected directory_path
        """
        is_lif = self.is_lif
        is_supported = True
        path = pathlib.Path(directory_path)
        # Lif Case
        if is_lif:
            self.output_dir = False
            working_directory = path.parent / "output/"
            os.makedirs(working_directory, exist_ok=True)
            if path.suffix.lower() == ".lif":
                # Extract from lif file all the single series images and extract to .tif, .tiff and .npy files into subdirectory
                extract_from_lif_file(lif_path=path, target_dir=working_directory)
            pass


        # Tiff Case
        else:
            if path.name == "output":
                self.gui.page.snack_bar = ft.SnackBar(ft.Text("The directory path output is not allowed!"))
                self.gui.page.snack_bar.open = True
                self.output_dir = True
                self.gui.page.update()
                self.gui.csp.image_paths = {}
                self.gui.csp.linux_images = {}
                self.gui.csp.mask_paths = {}
                return
            self.output_dir = False
            # Copy .tif, .tiff and .npy files into subdirectory
            working_directory = path / "output/"
            os.makedirs(working_directory, exist_ok=True)
            copy_files_between_directories(path, working_directory, file_types=[".tif", ".tiff", ".npy"])

            #converting the 16 bit images in 8 bit
            for path in working_directory.iterdir():
                converted = self.convert_tiffs_to_8_bit(path)
                is_supported = is_supported and converted


        self.gui.csp.working_directory = working_directory
        self.set_paths(is_supported)

    def select_directory_parallel(self, directory_path):
        """
            Gets the working directory and copies the images in their.

            Args:
                directory_path (str): the selected directory_path
                """
        is_lif = self.is_lif
        is_supported = True
        path = pathlib.Path(directory_path)
        # Lif Case
        if is_lif:
            self.output_dir = False
            working_directory = path.parent / "output/"
            os.makedirs(working_directory, exist_ok=True)
            if path.suffix.lower() == ".lif":
                # Extract from lif file all the single series images and extract to .tif, .tiff and .npy files into subdirectory
                extract_from_lif_file(lif_path=path, target_dir=working_directory)
            pass


        # Tiff Case
        else:
            if path.name == "output":
                self.gui.page.snack_bar = ft.SnackBar(ft.Text("The directory path output is not allowed!"))
                self.gui.page.snack_bar.open = True
                self.output_dir = True
                self.gui.page.update()
                self.gui.csp.image_paths = {}
                self.gui.csp.linux_images = {}
                self.gui.csp.mask_paths = {}
                return
            self.output_dir = False
            # Copy .tif, .tiff and .npy files into subdirectory
            working_directory = path / "output/"
            os.makedirs(working_directory, exist_ok=True)
            copy_files_between_directories(path, working_directory, file_types=[".tif", ".tiff", ".npy"])

            #convert the 16bit bit depth in 8 bit (parallel)
            with ThreadPoolExecutor() as executor:
                result = list(executor.map(self.convert_tiffs_to_8_bit,working_directory.iterdir()))
                if False in result:
                    is_supported=False

        self.gui.csp.working_directory = working_directory
        self.set_paths(is_supported)

    def convert_tiffs_to_8_bit(self, path):
        """
        handles when the conversion should happen
        Args:
            path (str): the selected directory_path
        """
        converted=True
        if path.suffix.lower() == ".tif" or path.suffix.lower() == ".tiff":
            if path.is_file():
                converted=transform_image_path(path, path)

            if Image.open(path).mode in ["L", "RGB"]:
                print("8 bit")
        return converted

    def set_paths(self, is_supported):
        """
        Updates the image and mask paths in csp (CellSePi).

        Args:
             is_supported (bool): True if the image types are supported.
        """
        bfc = self.gui.csp.config.get_bf_channel()
        cp = self.gui.csp.config.get_channel_prefix()
        ms = self.gui.csp.config.get_mask_suffix()
        working_directory = self.gui.csp.working_directory

        image_paths, mask_paths = load_directory(working_directory, bright_field_channel=bfc, channel_prefix=cp, mask_suffix=ms)
        self.gui.start_button.disabled=True
        self.gui.progress_bar_text.value = "Waiting for Input"
        if len(image_paths) == 0:
            self.gui.ready_to_start = False
            self.gui.page.snack_bar = ft.SnackBar(ft.Text("The directory contains no valid files with the current Channel Prefix!"))
            self.gui.page.snack_bar.open = True
            self.gui.page.update()
            self.count_results_txt.color = ft.Colors.RED
            if not self.is_lif:
                os.rmdir(self.gui.csp.working_directory)
        elif not is_supported:
            self.gui.ready_to_start = False
            self.gui.page.snack_bar = ft.SnackBar(ft.Text("The directory contains an unsupported file type. Only 8 or 16 bit .tiff files allowed."))
            self.gui.page.snack_bar.open = True
            self.count_results_txt.color = ft.Colors.RED
            self.gui.page.update()
            image_paths = {}
            mask_paths = {}
        else:
            self.count_results_txt.color = None
            if self.gui.csp.model_path is not None:
                self.gui.progress_bar_text.value = "Ready to Start"
                self.gui.start_button.disabled = False
            self.gui.ready_to_start = True

        self.gui.csp.image_paths = image_paths
        self.gui.csp.mask_paths = mask_paths
        print(f"Selected Directory: {working_directory}")
        print(f"This directory contains {len(image_paths)} unique image ids.")

        print(f"This directory contains {len(mask_paths)} unique mask ids.")

    #TODO review by Jenna: Ich würde hier anstatt den kompletten Code zu duplizieren die benötigten Änderungen ausführen in der if
    # und mir dann die gebrauchten images zwischenspeichern, sonst ist hier sehr viel Code doppelt, was auf den ersten Blick nicht nötig erscheint.
    def load_images(self):
        """
        Load images to gallery in order and with names.
        """
        self.image_gallery.controls.clear()
        self.gui.canvas.main_image.content = ft.Image(src=r"data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA\AAAFCAIAAAFe0wxPAAAAAElFTkSuQmCC",
                                    fit=ft.ImageFit.SCALE_DOWN)
        # the window of the image display is cleared of all content
        self.gui.switch_mask.value = False
        self.gui.canvas.container_mask.visible = False
        self.gui.csp.image_id = None
        self.gui.open_button.visible = False
        self.gui.drawing_button.disabled = True
        self.gui.page.update()
        self.check_masks()

        src = self.gui.csp.image_paths
        if platform.system() == "Linux":
            self.gui.csp.linux_images = convert_tiffs_to_png_parallel(self.gui.csp.image_paths)
            self.gui.csp.linux = True
            src = self.gui.csp.linux_images

        # Display groups with side-by-side images for linux
        for image_id in src:
            cur_image_paths = src[image_id]
            group_row = ft.Row(
                [
                    ft.Column(
                    [
                            ft.GestureDetector(
                                content=get_Image(self.gui.csp.linux,cur_image_paths[channel_id]),
                                on_tap=lambda e, img_id=image_id, c_id=channel_id: on_image_click(img_id, c_id,
                                                                                                  self.gui)
                            ),
                            ft.Text(channel_id, size=10, text_align="center"),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=5
                    )
                    for channel_id in cur_image_paths
                ],
                alignment=ft.MainAxisAlignment.START,
                spacing=10,
                scroll=ft.ScrollMode.AUTO,
            )
            self.image_gallery.controls.append(
                ft.Column(
                    [
                        ft.Text(f"{image_id}", weight="bold", text_align=ft.TextAlign.CENTER),
                        group_row
                    ],
                    spacing=10,
                    alignment=ft.MainAxisAlignment.CENTER
                )
            )


        self.image_gallery.update()
        self.update_results_text()

    def create_dir_row(self):
        """
        Creates the row for directory picking.
        """
        return ft.Row(
        [
            ft.ElevatedButton(
                "Open Directory",
                icon=ft.icons.FOLDER_OPEN,
                on_click=lambda _: self.get_directory_dialog.get_directory_path(),
                disabled=self.gui.page.web,
            ),
        ], alignment=ft.MainAxisAlignment.START  # Change alignment to extend fully to the left
    )
    def create_files_row(self):
        """
        Creates the row for file picking.
        """
        return ft.Row(
        [
            ft.ElevatedButton(
                "Pick File",
                icon=ft.icons.UPLOAD_FILE,
                on_click=lambda _: self.pick_files_dialog.pick_files(allow_multiple=False),
            )
        ], alignment=ft.MainAxisAlignment.START  # Change alignment to extend fully to the left
    )
    def create_handlers(self):
        """
        Creates the handlers.
        """
        self.get_directory_dialog = ft.FilePicker(on_result=lambda e: self.get_directory_result(e))
        self.pick_files_dialog = ft.FilePicker(on_result=lambda e: self.get_directory_result(e))
        #add the handlers to the page
        self.gui.page.overlay.extend([self.pick_files_dialog, self.get_directory_dialog])

    def update_view(self,e):
        """
        Changes the visibility of the directory/file picking.
        """
        if int(e.data) == 1:
            self.is_lif = True
            self.files_row.visible = True
            self.directory_row.visible = False
        else:
            self.is_lif = False
            self.files_row.visible = False
            self.directory_row.visible = True

        self.gui.page.update()



    def create_directory_container(self):
        return ft.Container(
                content=ft.Stack(
                    [
                        ft.Container(
                            content=ft.Column(
                                [
                                    self.path_list_tile,
                                    self.lif_row
                                ]
                            )
                        ),
                        ft.Container(
                            content=ft.Container(
                                content=ft.IconButton(
                                    icon=ft.icons.COPY,
                                    tooltip="Copy to clipboard",
                                    on_click=lambda e, g = self.gui: copy_directory_to_clipboard(e,g)
                                ),
                                alignment=ft.alignment.top_right,
                            )
                        )
                    ]

                ),
                padding=10,
            )

    def disable_path_choosing(self):
        """
        Disables everything related with path choosing.
        """
        self.path_list_tile.disabled = True
        self.lif_row.disabled = True
        self.toggle_slider_state(self.lif_slider,disabled=True)

        self.gui.page.update()

    def enable_path_choosing(self):
        """
        Activates everything related with path choosing.
        """
        self.path_list_tile.disabled = False
        self.lif_row.disabled = False
        self.toggle_slider_state(self.lif_slider,disabled=False)
        self.gui.page.update()

    def toggle_slider_state(self,slider, disabled):
        """
        Toggles slider state if it is active or not.

        Args:
            slider: Slider object.
            disabled: Boolean if the slider should be disabled.
        """
        if disabled:
            slider.on_change = None
            slider.thumb_color = ft.Colors.GREY_400
            self.lif_slider_blocker.visible = True
            for control in slider.controls:
                control.color = ft.Colors.GREY_700
        else:
            slider.on_change = self.update_view
            slider.thumb_color = ft.Colors.BLUE_400
            self.lif_slider_blocker.visible = False
            for control in slider.controls:
                control.color = None

    def check_masks(self):
        """
        Checks if all masks are there, if not the readout button is invisible.
        """
        if self.gui.csp.mask_paths is not None:
            bfc = self.gui.csp.config.get_bf_channel()
            all_mask_present = all(image_id in self.gui.csp.mask_paths and bfc in self.gui.csp.mask_paths[image_id] for image_id in self.gui.csp.image_paths)
            if all_mask_present:
                fluorescence_button.visible = True
                self.gui.diameter_text.value = AverageDiameter(self.gui.csp).get_avg_diameter()
                self.gui.diameter_display.visible = True
                self.gui.page.update()
            else:
                fluorescence_button.visible = False
            fluorescence_button.update()
            print(f"all_masks: {all_mask_present}")
    #test bench for the parallelization of select directory
    def benchmark_seq_and_par(self, path):
        """
        The method is only included for testing purposes.
        Comparison between the sequential and parallel selection of dictionary with tiff files.
        Is executed if a dictionary is selected in the CellSePi window.
        Args:
            path-the selected path in the GUI

        """

        #sequential iterations
        start_sequential = time()
        min_time_sequential = INFINITY
        max_time_sequential = 0
        for i in range(10):
            iteration_start_time_sequential = time()
            self.select_directory(path)
            iteration_end_time_sequential = time()

            if iteration_end_time_sequential - iteration_start_time_sequential < min_time_sequential:
                min_time_sequential = iteration_end_time_sequential - iteration_start_time_sequential

            if iteration_end_time_sequential - iteration_start_time_sequential > max_time_sequential:
                max_time_sequential = iteration_end_time_sequential - iteration_start_time_sequential

        end_sequential = time()
        total_time_sequential = end_sequential - start_sequential
        avg_time_sequential = total_time_sequential / 100

        #parallel iterations
        start_parallel = time()
        min_time_parallel=INFINITY
        max_time_parallel = 0
        for i in range(10):
            iteration_start_time_parallel = time()
            self.select_directory_parallel(path)
            iteration_end_time_parallel = time()

            if iteration_end_time_parallel-iteration_start_time_parallel < min_time_parallel:
                min_time_parallel = iteration_end_time_parallel-iteration_start_time_parallel

            if iteration_end_time_parallel - iteration_start_time_parallel > max_time_parallel:
                max_time_parallel = iteration_end_time_parallel - iteration_start_time_parallel

        end_parallel = time()
        total_time_parallel = end_parallel - start_parallel
        avg_time_sequential = total_time_sequential / 100

        print("Comparison total time:\n ")
        print(f"The sequential function needs {total_time_sequential:.6f} seconds\n")
        print(f"The parallel function needs {total_time_parallel:.6f} seconds\n")

        print("Comparison minimal time:\n")
        print(f"The minimal time the parallel function needs {min_time_parallel:.6f} seconds\n")
        print(f"The minimal time the sequential function needs {min_time_sequential:.6f} seconds\n")

        print("Comparison maximal time:\n")
        print(f"The maximal time the parallel function needs {max_time_parallel:.6f} seconds\n")
        print(f"The maximal time the sequential function needs {max_time_sequential:.6f} seconds\n")