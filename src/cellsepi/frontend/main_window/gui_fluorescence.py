import flet as ft
fluorescence_button= ft.ElevatedButton(text= "Readout",
                                       icon=ft.Icons.FILE_DOWNLOAD,
                                       tooltip="Readout fluorescence values",
                                       disabled=False,
                                       visible=False)

def error_banner(gui, message):
    gui.page.open(ft.SnackBar(
        ft.Text(message)))
    gui.page.update()