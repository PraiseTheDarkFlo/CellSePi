import multiprocessing

import flet as ft
from cellsepi.frontend.main_window.gui import GUI

def main():
    multiprocessing.set_start_method("spawn")
    ft.app(target=async_main, view=ft.FLET_APP)

async def async_main(page: ft.Page):
    gui = GUI(page)
    gui.build()
