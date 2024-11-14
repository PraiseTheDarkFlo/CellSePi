import flet as ft
from src.GUI.GUI import GUI

def main(page: ft.Page):
    gui = GUI(page)
    gui.build()
ft.app(target=main)
