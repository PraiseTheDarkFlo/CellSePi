import tkinter as tk
from tkinter import ttk

import numpy as np
from PIL import ImageTk, Image
import matplotlib.pyplot as plt


class TextInput(tk.Frame):

    def __init__(self, parent, label="", ipadx=2, ipady=2):
        super().__init__(parent)
        # self.frame = ttk.Frame(parent)
        self.columnconfigure(1, weight=1)

        self.label = tk.Label(self, text=label)
        self.label.grid(row=0, column=0, padx=0)
        self.string_var = tk.StringVar()
        self.entry = ttk.Entry(self, textvariable=self.string_var)
        self.entry.grid(row=0, column=1, padx=(ipadx, 0), sticky="news")

        pass


class ImageChannelView(tk.Frame):

    def __init__(self, parent, image_id, image_paths=None, bit_depth=16, ipadx=2, ipady=2, on_click_listener=None):
        super().__init__(parent)

        channel_ids = sorted(image_paths.keys())

        self.photo_images = []
        self.click_listeners = []

        text_label = tk.Label(self, text=f"{image_id}")
        text_label.grid(row=0, column=1, ipadx=2)

        for c_id in channel_ids:
            path = image_paths[c_id]

            image = Image.open(path)
            image = image.resize(size=(100, 100))

            image = Image.fromarray(np.uint8(np.array(image) / 2 ** (bit_depth - 8)))



            imageTk = ImageTk.PhotoImage(image)

            label = tk.Label(self, text=c_id, image=imageTk, height=100, width=100)
            label.image = imageTk
            label.grid(row=1, column=c_id, ipadx=2)
            if on_click_listener:
                cur_c_id = int(c_id)
                # def cur_on_click_listener(e):
                #     return on_click_listener(image_id, cur_c_id, e)
                click_listener = MyClickListener(image_id, cur_c_id, on_click_listener)
                # cur_on_click_listener = lambda e: on_click_listener(image_id, c_id, e)
                label.bind("<Button-1>",
                           click_listener
                           )
                self.click_listeners.append(click_listener)
            self.photo_images.append(label)
        #  print(self.click_listeners)


class MyClickListener:
    def __init__(self, image_id, c_id, on_click_listener):
        self.image_id = image_id
        self.c_id = c_id
        self.on_click_listener = on_click_listener

    def __call__(self, e, *args, **kwargs):
        print(self.image_id, self.c_id)
        result = self.on_click_listener(self.image_id, self.c_id, e)
        return result


class ScrollableFrame(tk.Frame):
    def __init__(self, parent, x=False, y=True):
        super().__init__(parent)

        canvas = tk.Canvas(self)  # , bg="red")
        canvas.pack(fill=tk.BOTH, expand=True)

        scrollbar_frame = tk.Frame(canvas)  # , bg="orange")
        scrollbar_frame.pack(expand=False, side=tk.LEFT)

        canvas.create_window((0, 0), window=scrollbar_frame, anchor="nw")

        if x:
            x_scrollbar = tk.Scrollbar(canvas, orient="horizontal", command=canvas.xview)
            x_scrollbar.pack(fill=tk.X, side=tk.BOTTOM)
            canvas.configure(yscrollcommand=x_scrollbar.set)

        if y:
            y_scrollbar = tk.Scrollbar(canvas, orient="vertical", command=canvas.yview)
            y_scrollbar.pack(fill=tk.Y, side=tk.RIGHT)
            canvas.configure(yscrollcommand=y_scrollbar.set)

        scrollbar_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        self.frame = scrollbar_frame
