import os.path
import pathlib
import threading
import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import askopenfilename, askdirectory

import matplotlib.pyplot as plt
import numpy as np
from PIL import ImageTk, Image

import custom_widgets_old
from data_util import load_directory, extract_from_lif_file, copy_files_between_directories
from image_processing_old import BatchImageSegmentation, BatchImageReadout
import torch


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.segmentation_running = False
        self.segmentation_thread = None
        self.readout_running = False
        self.readout_thread = None
        self.readout_path = None

        self.image_id = None
        self.channel_id = None
        self.image_view_update = True

        self.readout = None

        self.bit_depth = 16

        padx = 5
        pady = 2

        self.title("Image Processing Application")
        self.geometry("800x600")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        # self.rowconfigure(1, weight=1)
        self.columnconfigure(1, weight=1)

        # Left Panel
        self.left_panel = ttk.Frame(self, borderwidth=1, relief=tk.RAISED)
        self.left_panel.grid(row=0, column=0, sticky='nswe', padx=2, pady=2)

        self.image_view = tk.Frame(self.left_panel, borderwidth=1, relief=tk.RAISED)
        self.image_view.pack(fill='both', expand=True, padx=5, pady=5)
        # self.bright_field_channel = None
        # self.channel_prefix = None

        self.checkbutton_mask_var = tk.IntVar()
        self.checkbutton_mask = tk.Checkbutton(self.left_panel,
                                               text="Mask",
                                               padx=5,
                                               onvalue=1,
                                               offvalue=0,
                                               variable=self.checkbutton_mask_var,
                                               command=self.render_image_view)
        self.checkbutton_mask.pack(anchor=tk.W)

        self.checkbutton_is_lif_var = tk.IntVar()
        self.checkbutton_is_lif = tk.Checkbutton(self.left_panel,
                                                 text="Is Lif",
                                                 padx=5,
                                                 onvalue=1,
                                                 offvalue=0,
                                                 variable=self.checkbutton_is_lif_var,
                                                 command=self.render_image_view
                                                 )
        self.checkbutton_is_lif.pack(anchor=tk.W)

        self.text_input_bright_field_channel = custom_widgets.TextInput(self.left_panel, label="Bright Field Channel:")
        self.text_input_bright_field_channel.pack(fill="x", padx=padx, pady=pady)
        self.text_input_bright_field_channel.entry.insert(0, 1)

        self.text_input_channel_prefix = custom_widgets.TextInput(self.left_panel, label="Channel Prefix:")
        self.text_input_channel_prefix.pack(fill="x", padx=padx, pady=pady)
        self.text_input_channel_prefix.entry.insert(0, "c")

        self.text_input_mask_suffix = custom_widgets.TextInput(self.left_panel, label="Mask Suffix:")
        self.text_input_mask_suffix.pack(fill="x", padx=padx, pady=pady)
        self.text_input_mask_suffix.entry.insert(0, "_seg")

        self.text_input_diameter = custom_widgets.TextInput(self.left_panel, label="Diameter:")
        self.text_input_diameter.pack(fill="x", padx=padx, pady=pady)
        self.text_input_diameter.entry.insert(0, 250.0)

        self.directory = None
        self.working_directory = None
        self.file_selector_directory_button = ttk.Button(self.left_panel, text="Select File or Directory",
                                                         command=self.select_directory)
        self.file_selector_directory_button.pack(fill='x', padx=5, pady=2)

        self.model_path = None
        self.file_selector_model_button = ttk.Button(self.left_panel, text="Choose Model",
                                                     command=self.select_model)
        self.file_selector_model_button.pack(fill='x', padx=5, pady=2)
        self.file_selector_model_button["state"] = tk.DISABLED

        self.button_segment = ttk.Button(self.left_panel, text="Start Segmentation", command=self.segment_images)
        self.button_segment.pack(fill='x', padx=5, pady=2)
        self.button_segment["state"] = tk.DISABLED

        self.button_readout = ttk.Button(self.left_panel, text="Readout Fluorescence", command=self.readout_images)
        self.button_readout.pack(fill='x', padx=5, pady=2)
        self.button_readout["state"] = tk.DISABLED

        # Right Panel
        self.right_panel = ttk.Frame(self, borderwidth=1, relief=tk.RAISED)
        self.right_panel.grid(row=0, column=1, sticky='nswe', padx=2, pady=2)

        self.directory_name_label = ttk.Label(self.right_panel, text="Directory Name")
        self.directory_name_label.pack(fill='x', padx=5, pady=5)

        self.image_frame = ttk.Frame(self.right_panel, borderwidth=1, relief=tk.RAISED)
        self.image_frame.pack(fill='both', expand=True, padx=5, pady=5)

        self.s_frame = custom_widgets.ScrollableFrame(self.image_frame, x=True, y=True)
        self.s_frame.pack(fill="both", expand=True)

        # for iX in range(200):
        #     label = tk.Label(self.s_frame.frame, text=iX)
        #     label.pack(fill=tk.BOTH, expand=True)

        self.images = []
        self.image_paths = None
        self.mask_paths = None
        self.image_views = []

        # for i in range(12):  # Placeholder for 12 images
        #    pass
        # image_button = tk.PhotoImage(file=None)

        # command = lambda i=i: self.image_click_listener(i)
        # image_button.grid(row=i // 4, column=i % 4, padx=5, pady=5)
        # self.images.append(image_button)

        # image_path = "/Users/erik/Documents/Privat/Bilder/_DSF0013.jpg"
        # # image_path = "/Users/erik/Documents/Promotion/_Konferenzen/2023-09_IWBDA/Presentation/Figures/g16542.png"
        # # image = ImageTk.PhotoImage(Image.open(image_paths[channel_ids[0]]))
        # image = Image.open(image_path)
        # # image = image.resize((50, 50))
        # imageTk = ImageTk.PhotoImage(image)
        #
        # # photo_image = tk.PhotoImage(self, file=image_path)
        # self.label = tk.Label(self.image_frame,text=1, image=imageTk)
        # self.label.image = imageTk
        # # label = tk.Label(self, text=0, image=imageTk)
        # self.label.pack(side="bottom", fill="both", expand="yes")

        # Progress Bar
        self.progress_bar = ttk.Progressbar(self.right_panel, orient='horizontal', mode='determinate')
        self.progress_bar.pack(fill="x", padx=5, pady=2)
        # self.progress_bar.grid(row=1, column=0, columnspan=2, sticky='we', padx=5, pady=5)

    def select_directory(self):

        is_lif = bool(self.checkbutton_is_lif_var.get())
        if is_lif:
            path = askopenfilename()
        else:
            path = askdirectory()
        # print("Remove fixed dir")
        # dirname = "/Users/erik/Documents/Promotion/Projekte/Anjas_Stuff/Cellpose Train/"

        path = pathlib.Path(path)
        # Lif Case
        if path.is_file() and path.suffix == ".lif":
            working_directory = path.parent / "output/"
            os.makedirs(working_directory, exist_ok=True)
            # Extract from lif file all the single series images and extract to .tif, .tiff and .npy files into subdirectory
            extract_from_lif_file(lif_path=path, target_dir=working_directory)
            pass

        # Tiff Case
        if path.is_dir():
            # Copy .tif, .tiff and .npy files into subdirectory
            working_directory = path / "output/"
            os.makedirs(working_directory, exist_ok=True)
            copy_files_between_directories(path, working_directory, file_types=[".tif", ".tiff", ".npy"])

        self.directory = path
        self.working_directory = working_directory

        self.load_directory(working_directory)

    def load_directory(self, dirname):
        bfc = int(self.text_input_bright_field_channel.entry.get())
        cp = self.text_input_channel_prefix.entry.get()
        ms = self.text_input_mask_suffix.entry.get()

        image_paths, mask_paths = load_directory(dirname, bright_field_channel=bfc, channel_prefix=cp, mask_suffix=ms)
        self.image_paths = image_paths
        self.mask_paths = mask_paths
        print(f"Selected Directory: {dirname}")
        print(f"This directory contains {len(image_paths)} unique image ids.")
        print(f"This directory contains {len(mask_paths)} unique mask ids.")

        # Remove currently displayed images
        for image_view in self.image_views:
            image_view.destroy()

        is_lif = bool(self.checkbutton_is_lif_var.get())
        bit_depth = 8 if is_lif else 16
        self.bit_depth = bit_depth

        # Add new images
        self.image_views = []
        for image_id in image_paths:
            cur_image_paths = image_paths[image_id]
            image_channel_view = custom_widgets.ImageChannelView(self.s_frame.frame, image_id, cur_image_paths,
                                                                 bit_depth=bit_depth,
                                                                 on_click_listener=self.on_image_click)
            image_channel_view.pack(fill="x", pady=2)

            self.image_views.append(image_channel_view)
            pass

        self.file_selector_model_button["state"] = tk.ACTIVE

        self.button_readout["state"] = tk.ACTIVE
        return image_paths, mask_paths

    def on_image_click(self, image_id, channel_id, event):
        print(f"Image {image_id} (channel {channel_id}) selected.")

        self.image_id = image_id
        self.channel_id = channel_id

        self.render_image_view()
        pass

    def select_model(self):
        # Placeholder function for selecting model
        filename = askopenfilename()

        if os.path.isfile(filename):
            self.model_path = filename
        print(f"Model selected: {filename}")
        self.button_segment["state"] = tk.ACTIVE

    def segment_images(self):
        def on_update(progress, current_image):
            print(f"Completed {progress} % of images")
            self.update_progress_bar(progress)

            pass

        def on_completion(mask_paths, **kwargs):
            print("Completed Segmentation")
            # self.update_progress_bar(100)
            self.mask_paths = mask_paths
            self.segmentation_running = False
            self.button_segment["state"] = tk.NORMAL

            self.load_directory(self.working_directory)
            pass

        # Do not start segmentation if it is already running
        if self.segmentation_running:
            print("Segmentation already running")
            return

        # Check that segmentation thread is free
        if self.segmentation_thread is not None:
            if self.segmentation_thread.is_alive():
                print("Segmentation Thread already occupied, please try again later.")

        print("Preparing Segmentation")
        self.segmentation_running = True
        self.button_segment["state"] = tk.DISABLED

        # Start Segmentation here
        segmentation_channel = int(self.text_input_bright_field_channel.entry.get())
        diameter = float(self.text_input_diameter.entry.get())
        device = "cpu"

        batch_image_segmentation = BatchImageSegmentation(image_paths=self.image_paths,
                                                          segmentation_channel=segmentation_channel,
                                                          diameter=diameter,
                                                          device=device,
                                                          segmentation_model=None)

        batch_image_segmentation.add_update_listener(listener=on_update)
        batch_image_segmentation.add_completion_listener(listener=on_completion)

        target = batch_image_segmentation.run
        self.segmentation_thread = threading.Thread(target=target)

        print("Starting Segmentation")
        self.segmentation_thread.start()

    def readout_images(self):
        # Placeholder function for reading out images

        def on_update(progress, current_image):
            print(f"Completed {progress} % of images")
            self.update_progress_bar(progress)

            pass

        def on_completion(readout, readout_path, **kwargs):
            print("Completed Readout")
            # self.update_progress_bar(100)
            self.readout = readout
            self.readout_running = False
            self.button_readout["state"] = tk.NORMAL

            self.readout_path = readout_path
            print(f"Saved Readout to {readout_path}")

            pass

            # Do not start segmentation if it is already running

        if self.readout_running:
            print("Readout already running")
            return

            # Check that segmentation thread is free
        if self.readout_thread is not None:
            if self.readout_thread.is_alive():
                print("Readout Thread already occupied, please try again later.")

        if self.image_paths is None or len(self.image_paths) == 0:
            print("No images to process.")
            return

        print("Preparing Readout")
        self.readout_running = True
        self.button_readout["state"] = tk.DISABLED

        # Start Readout here
        segmentation_channel = int(self.text_input_bright_field_channel.entry.get())
        cp = self.text_input_channel_prefix.entry.get()
        working_directory = self.working_directory

        batch_image_readout = BatchImageReadout(image_paths=self.image_paths,
                                                mask_paths=self.mask_paths,
                                                segmentation_channel=segmentation_channel,
                                                channel_prefix=cp,
                                                directory=working_directory)

        batch_image_readout.add_update_listener(listener=on_update)
        batch_image_readout.add_completion_listener(listener=on_completion)

        target = batch_image_readout.run
        self.readout_thread = threading.Thread(target=target)
        # target()

        print("Starting Readout")
        self.readout_thread.start()

    def image_click_listener(self, image_id):
        # Placeholder function for image click listener
        print(f"Image {image_id + 1} clicked")

    def update_progress_bar(self, value):
        self.progress_bar['value'] = value

    def render_image_view(self):
        # if not self.image_view_update:
        #     self.after(100, self.render_image_view)
        #     return
        #
        # self.image_view_update = False

        is_lif = bool(self.checkbutton_is_lif_var.get())
        self.text_input_bright_field_channel.entry.delete(0, tk.END)
        self.text_input_diameter.entry.delete(0, tk.END)
        if is_lif:
            self.text_input_bright_field_channel.entry.insert(0, 2)
            self.text_input_diameter.entry.insert(0, 125.0)
        else:
            self.text_input_bright_field_channel.entry.insert(0, 1)
            self.text_input_diameter.entry.insert(0, 250.0)



        display_mask = bool(self.checkbutton_mask_var.get())
        print(f"Display Mask: {display_mask}")

        for elem in list(self.image_view.children.values()):
            elem.destroy()

        image_id = self.image_id
        channel_id = self.channel_id
        bfc = int(self.text_input_bright_field_channel.entry.get())


        height_px = self.image_view.winfo_height()
        width_px = self.image_view.winfo_width()
        size = min([height_px, width_px])

        if self.image_paths is None or image_id not in self.image_paths:
            return
        path = self.image_paths[image_id][channel_id]

        bit_depth = self.bit_depth

        image = Image.open(path)
        image = Image.fromarray(np.uint8(np.array(image) / 2 ** (bit_depth - 8)))
        rgbimage = Image.new("RGBA", image.size)
        rgbimage.paste(image)

        if display_mask and image_id in self.mask_paths:
            mask_data = np.load(self.mask_paths[image_id][bfc], allow_pickle=True).item()
            mask = mask_data["masks"]
            outline = mask_data["outlines"]

            mask_ids = np.unique(mask)[1:]
            image_mask = np.zeros(shape=(mask.shape[0], mask.shape[1], 4), dtype=np.uint8)
            image_mask[mask != 0] = (255, 0, 0, 128)
            image_mask[outline != 0] = (0, 255, 0, 255)
            image_mask = Image.fromarray(image_mask, "RGBA")
            rgbimage.paste(image_mask, (0, 0), image_mask)
            pass

        rgbimage = rgbimage.resize(size=(size, size))
        imageTk = ImageTk.PhotoImage(rgbimage)

        label = tk.Label(self.image_view, text=channel_id, image=imageTk, height=100, width=100)
        label.image = imageTk
        label.pack(expand=True, fill=tk.BOTH)

        # self.after(100, self.render_image_view)



if __name__ == "__main__":
    app = App()
    app.mainloop()
