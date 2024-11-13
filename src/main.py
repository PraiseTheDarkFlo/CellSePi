
import flet as ft

from src.CellSePi import CellSePi


def main(page: ft.Page):
    csp = CellSePi(page)
    csp.gui.build()
ft.app(target=main)
