from collections import defaultdict

import flet as ft
from flet_contrib.color_picker import ColorPicker
from enum import Enum

from cellsepi.frontend.main_window.gui_mask import handle_mask_update


def hex_to_rgb(hex_color):
    """
    Converts a hex color string to rgb color

    Args:
        hex_color (str)

    Returns:
        rgb_color (tuple)
    """
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(rgb_color):
    """
    Converts a rgb color to hex color
    Args:
        rgb_color (tuple)
    Returns:
        hex_color (str)
    """
    return "#{:02x}{:02x}{:02x}".format(*rgb_color)

class ColorTypes(Enum):
    Mask = 1
    Outline = 2

class ColorSelection:
    def __init__(self,gui):
        self.config = gui.csp.config
        self.gui = gui
        color_mask = rgb_to_hex(self.config.get_mask_color())
        color_outline = rgb_to_hex(self.config.get_outline_color())
        self.color_picker = ColorPicker(color=color_mask, width=430)
        self.color_picker.hex.border_color=ft.colors.BLUE_ACCENT
        self.color_picker.r.border_color=ft.colors.BLUE_ACCENT
        self.color_picker.g.border_color=ft.colors.BLUE_ACCENT
        self.color_picker.b.border_color=ft.colors.BLUE_ACCENT
        self.color_icon_mask = ft.IconButton(icon=ft.icons.BRIGHTNESS_1_ROUNDED,icon_color=color_mask, on_click=self.open_color_picker_mask)
        self.color_icon_outline = ft.IconButton(icon=ft.icons.BRIGHTNESS_1_ROUNDED, icon_color=color_outline, on_click=self.open_color_picker_outline)
        self.color_type = None
        self.dialog = ft.CupertinoBottomSheet(
            content=ft.Column([ft.Card(content=ft.Stack([ft.Container(ft.ListTile(height=370,width=430),padding=10),ft.Container(ft.Column(
                [self.color_picker,
                ft.Container(ft.Row([ft.TextButton("Save", on_click=self.change_color)
                 ],alignment=ft.MainAxisAlignment.END),padding=10)
                ]
            ),height=430,width=450,padding=10)]))],horizontal_alignment=ft.CrossAxisAlignment.CENTER,alignment=ft.MainAxisAlignment.CENTER),
            on_dismiss=self.close_dialog,
        )
    def open_color_picker_mask(self,e):
        e.control.page.open(self.dialog)
        self.color_picker.color = rgb_to_hex(self.config.get_mask_color())
        self.color_type = ColorTypes.Mask
        self.dialog.open = True
        e.control.page.update()


    def open_color_picker_outline(self, e):
        e.control.page.open(self.dialog)
        self.color_picker.color = rgb_to_hex(self.config.get_outline_color())
        self.color_type = ColorTypes.Outline
        self.dialog.open = True
        e.control.page.update()

    def change_color(self, e):

        """
        Standard color: Mask outline= green, Filling: red
            if it is reasonable, change the color to the liking
        Attributes:
            self.color_picker (ColorPicker)
        """
        if self.color_type == ColorTypes.Mask:
            self.color_icon_mask.icon_color = self.color_picker.color
            self.config.set_mask_color(hex_to_rgb(self.color_picker.color))
            self.gui.mask.mask_outputs = defaultdict(dict)
            handle_mask_update(self.gui)
            self.gui.queue.put(("color_change", self.config.get_mask_color(), self.config.get_outline_color()))
        else:
            self.color_icon_outline.icon_color = self.color_picker.color
            self.config.set_outline_color(hex_to_rgb(self.color_picker.color))
            self.gui.mask.mask_outputs = defaultdict(dict)
            handle_mask_update(self.gui)
            self.gui.queue.put(("color_change", self.config.get_mask_color(), self.config.get_outline_color()))
        e.control.page.close(self.dialog)
        e.control.page.update()

    def close_dialog(self, e):
        e.control.page.close(self.dialog)
        self.dialog.update()

class ColorOpacity:
    def __init__(self,gui):
        self.gui = gui
        self.slider = ft.Slider(
            min=10, max=128, value=128, width=142,
            on_change=lambda _: self.opacity_change()
        )
        self.text = ft.Container(
            content=ft.Text("Mask Opacity"),
            alignment=ft.alignment.center
        )

    def opacity_change(self):
        self.gui.csp.color_opacity = self.slider.value
        handle_mask_update(self.gui)