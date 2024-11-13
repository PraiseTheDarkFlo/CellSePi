from functools import partial

import flet as ft
import os

from . import gui_options as op
from .gui_canvas import Canvas
from .gui_directory import format_directory_path, copy_directory_to_clipboard, create_directory_card
from .gui_segmentation import create_segmentation_card
from .. import CellSePi


class GUI:
    def __init__(self, csp: CellSePi,page: ft.Page):
        self.csp = csp
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

    def build(self):

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
            options=[  # hier sollte je nach den bilder auswählbar sein welches bild das BrightFiled Channel ist...
                ft.dropdown.Option("1"),
                ft.dropdown.Option("2"),
                ft.dropdown.Option("3"),
                ft.dropdown.Option("4"),
            ],
            border_color=ft.colors.BLUE_ACCENT
        )

        def update_view_mask(e):
            if self.switch_mask.value:
                print("on")
            else:
                print("off")
            self.page.update()

        self.page.add(
            ft.Column(  # Hauptspalte für die gesamte UI
                [
                    ft.Row(  # Linke und rechte Seite in einer Zeile anordnen
                        [
                            ft.Column(  # Linke Spalte mit Steuerungselementen
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
                            ft.Column(  # Rechte Spalte mit Galerie und Verzeichnispfad
                                [
                                    self.directory_card,
                                    ft.Card(  # Galerie als Container
                                        content=self.image_gallery,
                                        width=self.page.width * (1 / 3),
                                        expand=True,
                                        aspect_ratio=4
                                    ),
                                ],
                                expand=True,
                            ), op.switch(self.page)
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,  # Abstand zwischen linkem und rechtem Bereich
                        expand=True,
                    ),
                ],
                expand=True
            )
        )

        # Initiale Sichtbarkeit setzen
        self.switch_mask.on_change = update_view_mask


