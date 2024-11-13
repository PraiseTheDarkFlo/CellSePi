import flet as ft
from . import GUI

def create_segmentation_card(gui: GUI):
    def pick_model_result(e: ft.FilePickerResultEvent):
        # TODO
        print("pick Model")
        pass

    pick_model_dialog = ft.FilePicker(on_result=pick_model_result)
    gui.page.overlay.extend([pick_model_dialog])

    pick_model_row = ft.Row(
        [
            # wenn es läuft könnte man anstatt Start segmentation cancel machen und progressbar nur wenn es gestartet ist sonst nur start button
            ft.ProgressBar(value=0.2, width=180),
            ft.Text("2%"),
            ft.ElevatedButton(
                "Start Segmentation",
                icon=ft.icons.PLAY_CIRCLE,
                disabled=True,
                on_click=lambda _: pick_model_dialog.pick_files(allow_multiple=False),
            )
        ], alignment=ft.MainAxisAlignment.END
    )

    return ft.Card(
        content=ft.Container(
            content=ft.Stack(
                [
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.ListTile(
                                    leading=ft.Icon(name=ft.icons.COMPUTER_ROUNDED),
                                    title=ft.Text("Model Name"),
                                ),
                                pick_model_row,
                            ]
                        )
                    ),
                    ft.Container(
                        content=ft.IconButton(
                            icon=ft.icons.UPLOAD_FILE,
                            tooltip="Chose Model",
                            on_click=lambda _: pick_model_dialog.pick_files(allow_multiple=False),
                        ), alignment=ft.alignment.bottom_right,
                    )
                ]
            ),
            width=gui.page.width * (1 / 3),
            padding=10
        ),
    )