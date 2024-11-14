from functools import partial

import flet as ft
import os

from . import gui_options as op
from .gui_canvas import Canvas
from .gui_directory import format_directory_path, copy_directory_to_clipboard, create_directory_card
from .gui_segmentation import create_segmentation_card
from .. import CellSePi

#class GUI to handle the complete GUI and their attributes, also contains the CellSePi class and updates their attributes
class GUI:
    def __init__(self,page: ft.Page):
        self.csp = CellSePi
        self.page = page
        self.directory_path = ft.Text(weight="bold",value='Directory Path')
        self.image_gallery = ft.ListView()
        self.count_results_txt = ft.Text(value="Results: 0")
        self.is_lif = ft.Switch(label="Lif", value=True)
        self.switch_mask = ft.Switch(label="Mask", value=True)
        self.page.window.width = 1200
        self.page.window.height = 825
        self.page.window.min_width = self.page.window.width
        self.page.window.min_height = self.page.window.height
        self.page.title = "CellSePi"
        self.formatted_path = ft.Text(format_directory_path(self.directory_path), weight="bold")
        self.directory_card = create_directory_card(self)
        self.canvas = Canvas()
        self.segmentation_card = create_segmentation_card(self)

    def build(self): #build up the main page of the GUI
        tf_cp = ft.TextField(
            label="Channel Prefix:",
            border_color=ft.colors.BLUE_ACCENT
        )
        tf_d = ft.TextField(
            label="Diameter:",
            border_color=ft.colors.BLUE_ACCENT
        )
        tf_ms = ft.TextField(
            label="Masked Suffix:",
            border_color=ft.colors.BLUE_ACCENT
        )
        dropdown_bf_channel = ft.Dropdown(
            label="Bright Field Channel:",
            options=[
                ft.dropdown.Option("1"),
                ft.dropdown.Option("2"),
                ft.dropdown.Option("3"),
                ft.dropdown.Option("4"),
            ],
            border_color=ft.colors.BLUE_ACCENT
        )


        self.page.add(
            ft.Column(
                [
                    ft.Row(
                        [
                            #LEFT COLUMN that handles all elements on the left side(canvas,switch_mask,segmentation)
                            ft.Column(
                                [
                                    self.canvas.canvas_card
                                    ,
                                    ft.Row([self.switch_mask]),
                                    ft.Row([dropdown_bf_channel, tf_cp]),
                                    ft.Row([tf_ms, tf_d]),
                                    self.segmentation_card
                                ],
                                expand=True,
                                alignment=ft.MainAxisAlignment.START,
                            ),
                            #RIGHT COLUMN that handles gallery and directory_card
                            ft.Column(
                                [
                                    self.directory_card,
                                    ft.Card(
                                        content=self.image_gallery,
                                        width=self.page.width * (1 / 3),
                                        expand=True,
                                        aspect_ratio=4
                                    ),
                                ],
                                expand=True,
                            ), op.switch(self.page)
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        expand=True,
                    ),
                ],
                expand=True
            )
        )
        #method that controls what happened when switch is on/off
        def update_view_mask(e):
            if self.switch_mask.value:
                print("on")
            else:
                print("off")
            self.page.update()

        self.switch_mask.on_change = update_view_mask


