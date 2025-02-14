import multiprocessing
import flet as ft
from src.frontend.main_window.gui import GUI

if __name__ == '__main__':
    async def main(page: ft.Page):
        gui = GUI(page)
        gui.build()
    multiprocessing.set_start_method("spawn")
    ft.app(target=main, view=ft.FLET_APP)
