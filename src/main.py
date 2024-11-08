import flet as ft

from src.CellSePi import CellSePi
from src.GUI.gui import gui


def main(page: ft.Page):
    page.window.width = 1200
    page.window.height = 825
    page.window.min_width = page.window.width
    page.window.min_height = page.window.height
    page.title = "CellSePi"
    directory_path = ft.Text(weight="bold",value='Directory Path')
    image_gallery = ft.ListView()
    gui(page, image_gallery, directory_path)

ft.app(target=main)
