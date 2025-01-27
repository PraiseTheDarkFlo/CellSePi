import multiprocessing

import flet as ft
from src.GUI.GUI import GUI

if __name__ == '__main__':
    async def main(page: ft.Page):
        gui = GUI(page)
        await gui.build()
    multiprocessing.set_start_method("spawn")
    ft.app(target=main, view=ft.FLET_APP)
