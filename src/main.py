import multiprocessing

import flet as ft
from src.GUI.GUI import GUI

if __name__ == '__main__':
    def main(page: ft.Page):
        gui = GUI(page)
        gui.build()
    multiprocessing.set_start_method("spawn")
    ft.app(target=main)
