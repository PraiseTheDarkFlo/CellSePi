import multiprocessing
import sys

import flet as ft
from cellsepi.frontend.main_window.gui import GUI
from cellsepi.cli import build as flet_build

def main():
    if len(sys.argv) > 1 and sys.argv[1].lower() == "build":
        flet_build()
    else:
        multiprocessing.set_start_method("spawn")
        ft.app(target=async_main, view=ft.FLET_APP)

async def async_main(page: ft.Page):
    gui = GUI(page)
    gui.build()
