import flet as ft
fluorescence_button= ft.ElevatedButton(text= "Readout",
                                       icon=ft.icons.FILE_DOWNLOAD,
                                       tooltip="Readout fluorescence values",
                                       disabled=False,
                                       visible=False)

def error_banner(gui, message):
    gui.page.snack_bar = ft.SnackBar(
        ft.Text(message))
    gui.page.snack_bar.open = True
    gui.page.update()