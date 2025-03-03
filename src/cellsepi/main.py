import flet as ft
from cellsepi.frontend.main_window.gui import GUI

async def main(page: ft.Page):
    gui = GUI(page)
    gui.build()
