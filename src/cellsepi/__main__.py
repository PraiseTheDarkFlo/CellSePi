import flet as ft
from cellsepi.main import main
import multiprocessing

if __name__ == "__main__":
    multiprocessing.set_start_method("spawn")
    ft.app(target=main, view=ft.FLET_APP)
