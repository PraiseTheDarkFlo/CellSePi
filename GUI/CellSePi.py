import flet as ft
import gui

import flet as ft

def main_gui(page: ft.Page):
    page.window.width = 1200
    page.window.height = 825
    page.window.min_width = page.window.width
    page.window.min_height = page.window.height
    page.title = "CellSePi"
    directory_path = ft.Text(weight="bold",value='Directory Path')
    image_gallery = ft.ListView()
    gui.gui(page,image_gallery,directory_path)

ft.app(target=main_gui)


