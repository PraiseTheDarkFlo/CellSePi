
import flet as ft
import GUI


fluorescence_button= ft.ElevatedButton(text= "Readout Fluorescence",
                                                    icon=ft.icons.FILE_DOWNLOAD,
                                                    disabled=False,
                                                    visible=True)

def error_banner(gui:GUI, message):
    gui.page.snack_bar = ft.SnackBar(
        ft.Text(message))
    gui.page.snack_bar.open = True
    gui.page.update()