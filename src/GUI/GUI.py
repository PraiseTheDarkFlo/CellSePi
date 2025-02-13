import asyncio
import atexit
import multiprocessing
import os
import threading

import flet as ft
from flet_core import BoxShape

from .gui_options import Options
from .gui_segmentation import GUISegmentation
from .drawing.gui_drawing import open_qt_window
from .gui_canvas import Canvas
from .gui_config import GUIConfig
from .gui_directory import DirectoryCard, copy_to_clipboard
from src.CellSePi import CellSePi
from src.mask import Mask
from .gui_mask import error_banner,handle_image_switch_mask_on, handle_mask_update
from ..avg_diameter import AverageDiameter
from ..image_tuning import ImageTuning, AutoImageTuning
from .gui_test_environment import Testing




class GUI:
    """
    Class GUI to handle the complete GUI and their attributes, also contains the CellSePi class and updates their attributes
    """
    def __init__(self,page: ft.Page):
        self.csp: CellSePi = CellSePi()
        self.page = page
        self.directory = DirectoryCard(self)
        self.switch_mask = ft.Switch(label="Mask", value=False)
        self.switch_mask.on_change = lambda e: self.update_view_mask()
        self.queue = multiprocessing.Queue()
        parent_conn, child_conn = multiprocessing.Pipe()
        self.parent_conn, self.child_conn = parent_conn, child_conn
        self.cancel_event = None
        self.closing_event = False
        self.pipe_listener_running = True
        self.thread = threading.Thread(target=self.child_conn_listener, daemon=True)
        self.thread.start()
        self.page.window.prevent_close = True
        self.page.window.on_event = lambda e: self.handle_closing_event(e)
        self.process_drawing_window = self.start_drawing_window()
        self.drawing_button= ft.ElevatedButton(text="Drawing Tools", icon="brush_rounded",on_click=lambda e: self.set_queue_drawing_window(),disabled=True)
        self.page.window.width = 1408
        self.page.window.height = 800
        self.page.window.center()
        self.page.window.min_width = self.page.window.width
        self.page.window.min_height = self.page.window.height
        self.page.title = "CellSePi"
        self.canvas = Canvas()
        self.op = Options(self)
        self.test_environment=Testing(self)
        gui_config = GUIConfig(self)
        self.gui_config = gui_config.create_profile_container()
        self.segmentation = GUISegmentation(self)
        seg_card,start_button,open_button,progress_bar,progress_bar_text,cancel_segmentation = self.segmentation.create_segmentation_card()
        self.cancel_segmentation = cancel_segmentation
        self.ready_to_start = False
        self.segmentation_card = seg_card
        self.open_button = open_button
        self.start_button = start_button
        self.progress_bar = progress_bar
        self.progress_bar_text = progress_bar_text
        self.mask=Mask(self.csp)
        self.image_tuning = ImageTuning(self)
        self.progress_ring = ft.ProgressRing(visible=False)
        self.closing_sheet = ft.CupertinoBottomSheet(
            content=ft.Column([ft.ProgressRing()],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            modal=True,
        )
        self.brightness_slider = ft.Slider(
            min=0, max=2.0, value=1.0, disabled= True,
            on_change=lambda e: asyncio.run(self.image_tuning.update_main_image_async())
        )
        self.contrast_slider = ft.Slider(
            min=0, max=2.0, value=1.0, disabled= True,
            on_change=lambda e: asyncio.run(self.image_tuning.update_main_image_async())
        )
        self.auto_image_tuning = AutoImageTuning(self)
        self.auto_brightness_contrast = ft.IconButton(icon=ft.Icons.AUTO_FIX_HIGH,icon_color=ft.Colors.GREY_700,style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=12),
                ),on_click=lambda e: self.auto_image_tuning.pressed(),tooltip="Auto brightness and contrast")
        self.brightness_icon = ft.Icon(name=ft.icons.SUNNY,tooltip="Brightness")
        self.contrast_icon = ft.Icon(name=ft.icons.CONTRAST,tooltip="Contrast")
        self.diameter_text = ft.Text("0", size=14, weight=ft.FontWeight.BOLD,tooltip="Copy to clipboard")
        self.diameter_display = ft.Container(
            content=ft.Row([ft.Icon(name=ft.icons.STRAIGHTEN_ROUNDED, tooltip="Average diameter"), ft.GestureDetector(content=self.diameter_text,on_tap=lambda e: copy_to_clipboard(page=self.page,value=str(self.diameter_text.value),name="Average diameter"),on_enter=lambda e:self.on_enter_diameter(),on_exit=lambda e:self.on_exit_diameter()),]),
            border_radius=12,
            padding=8,
            visible=True,
        )
        if self.csp.config.get_auto_button():
            self.auto_image_tuning.pressed()

    def build(self):
        """
        Build up the main page of the GUI
        """
        self.page.add(
            ft.Column(
                [
                    ft.Row(
                        [
                            #LEFT COLUMN that handles all elements on the left side(canvas,switch_mask,segmentation)
                            ft.Column(
                                [
                                    self.canvas.canvas_card,
                                    ft.Row([self.switch_mask, self.drawing_button]),
                                    ft.Row([self.gui_config,ft.Column([ft.Card(content=ft.Container(content=ft.Column([ft.Row([self.brightness_icon,ft.Container(self.brightness_slider,padding=-15)]),ft.Row([self.contrast_icon,ft.Container(self.contrast_slider,padding=-15)])]),padding=10)),
                                                                       ft.Row([ft.Card(content=self.auto_brightness_contrast), ft.Card(content=self.diameter_display)])])
                                            ]),
                                    self.segmentation_card
                                ],
                                expand=True,
                                alignment=ft.MainAxisAlignment.START,
                            ),
                            #RIGHT COLUMN that handles gallery and directory_card
                            ft.Column(
                                [
                                    self.directory,
                                    ft.Card(
                                        content=ft.Stack([ft.Container(self.progress_ring,alignment=ft.alignment.center),ft.Container(self.directory.image_gallery,padding=20)]),
                                        expand=True
                                    ),
                                ],
                                expand=True,
                            ),
                            ft.Column([self.op,self.test_environment]),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        expand=True,
                    ),
                ],
                expand=True
            )
        )

    def update_view_mask(self):
        """
        Method that controls what happened when switch is on/off
        """
        if self.csp.image_id is None:
            print("No image selected")
            error_banner(self,"No image selected!")
            self.switch_mask.value=False
        else:
            handle_image_switch_mask_on(self)

    def start_drawing_window(self):
        """
        Start the drawing window in multiprocessing.
        """
        process = multiprocessing.Process(target=open_qt_window,
                                args=(self.queue,self.child_conn))
        process.start()
        return process

    def set_queue_drawing_window(self):
        """
        Sets queue for drawing window with the current selected image and mask.
        """
        self.image_tuning.save_current_main_image()
        if self.process_drawing_window is None or not self.process_drawing_window.is_alive(): #make sure that the process is running before putting new image in the queue
            print("Process is not alive, restarting...")
            if self.process_drawing_window is not None:
                try:
                    self.process_drawing_window.terminate()
                    self.process_drawing_window.join()
                except Exception as e:
                    print(f"Error while terminating process: {e}")
            self.queue = multiprocessing.Queue()
            parent_conn, child_conn = multiprocessing.Pipe()
            self.parent_conn, self.child_conn = parent_conn, child_conn
            self.process_drawing_window = self.start_drawing_window()
        self.csp.window_image_id = self.csp.image_id
        self.csp.window_bf_channel = self.csp.config.get_bf_channel()
        self.csp.window_channel_id = self.csp.channel_id

        if self.csp.window_bf_channel in self.csp.image_paths[self.csp.image_id]:#check if the bf has an image
            image_path = self.csp.image_paths[self.csp.image_id][self.csp.window_bf_channel]
            directory, filename = os.path.split(image_path)
            name, _ = os.path.splitext(filename)
            mask_file_name = f"{name}{self.csp.config.get_mask_suffix()}.npy"
            mask_path= os.path.join(directory, mask_file_name)
            self.queue.put((self.csp.config.get_mask_color(), self.csp.config.get_outline_color(), self.csp.window_bf_channel, self.csp.mask_paths, self.csp.window_image_id, self.csp.adjusted_image_path, mask_path,self.csp.window_channel_id,self.csp.current_channel_prefix))
        else:
            self.page.snack_bar = ft.SnackBar(
                ft.Text(f"Selected bright-field channel {self.csp.window_bf_channel},has no image!"))
            self.page.snack_bar.open = True
            self.page.update()

    def handle_closing_event(self, e):
        """
        Handle the closing event of Flet GUI.
        """
        if e.data == "close" and not self.closing_event:
            self.closing_event = True
            self.page.open(self.closing_sheet)
            if self.csp.segmentation_running:
                self.cancel_event = multiprocessing.Event()
                self.cancel_segmentation()
                self.cancel_event.wait()
                print("cancel wait")
            self.pipe_listener_running = False
            self.queue.put("close")
            print("test before drawing")
            if self.process_drawing_window is not None and self.process_drawing_window.is_alive():
                self.process_drawing_window.join()
            print("test5")
            self.child_conn.send("close")

            if self.thread is not None and self.thread.is_alive():
                self.thread.join()
            self.child_conn.close()
            self.parent_conn.close()
            # TODO: close everything that have threads e.g. cellpose and diameter calc or image_tuning(but image tuning is fast not necessary to end i think)
            # TODO: block here some where until every thing is no longer running
            self.page.window.destroy()
            print("closing window finished")



    def child_conn_listener(self):
        """
        Listener for the child connection.
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        async def pipe_listener():
            while self.pipe_listener_running:
                data = await asyncio.to_thread(self.parent_conn.recv)
                print(f"Empfangene Daten: {data}")
                split_data = data.split(".")
                if data == "close":
                    break
                elif split_data[0] == "new_mask":
                    if self.csp.window_image_id not in self.csp.mask_paths:
                        self.csp.mask_paths[self.csp.window_image_id] = {}
                    self.csp.mask_paths[self.csp.window_image_id][self.csp.window_bf_channel] = self.csp.window_mask_path
                    self.directory.update_mask_check(split_data[1])
                    print("in pipeline", split_data[1])
                else:
                    #if data is not closed and the window remains open: the edited image gets updated in the flet canvas
                    if self.csp.window_image_id == self.csp.image_id and self.csp.window_bf_channel == self.csp.config.get_bf_channel() and self.switch_mask.value:
                        print("update Mask flet")
                        #self.csp.mask_paths[self.csp.image_id][self.csp.config.get_bf_channel()]= r"C:\Users\Jenna\Studium\FS5\data\data\output\Series003c2_seg.npy"
                        handle_mask_update(self)

                        self.page.update()
                        #TODO: bzw. maske muss auch neu geladen werden wenn nicht aktiviert und nicht main image muss im hintergrund bild neu geladen werden also eigentlich aus dieser if raus
                        #bzw zwei methoden eins für aktiv picture dass gleich neu gleaden wird und eine für wenn bild nicht aktiv muss trotzdem neu generiert werden, also maybe dann speicher reseten oder so?
                        #TODO: hier mask updaten in Flet

                    #TODO: hier diameter neu berechnen
                    self.diameter_text.value = AverageDiameter.get_avg_diameter()
                    self.diameter_display.visible = True
        try:
            loop.run_until_complete(pipe_listener())
        finally:
            loop.stop()
            loop.close()

    def on_enter_diameter(self):
        self.diameter_text.color = ft.Colors.BLUE_400
        self.diameter_text.update()
    def on_exit_diameter(self):
        self.diameter_text.color = None
        self.diameter_text.update()
