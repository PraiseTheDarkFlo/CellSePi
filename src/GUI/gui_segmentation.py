import flet as ft
from . import GUI
from ..fluorescence import Fluorescence
from ..segmentation import segmentation


#build the segmentation_card with all events methods
def create_segmentation_card(gui: GUI):

    #method that does something with the result of the selection of the FIle
    def pick_model_result(e: ft.FilePickerResultEvent):
        if e.files[0].path != None:
            print("picked file")
            gui.csp.model_path = e.files[0].path
            progress_bar_text.value = "Ready to Start"
            start_button.disabled = False
            start_button.visible = True
            model_text.title.value = e.files[0].name
            gui.page.update()
            print("start_button is disabled", start_button.disabled)
            #TODO name des ausgewählten modells soll angezeigt werden
        else:
            print("no model selected")



    pick_model_dialog = ft.FilePicker(on_result=pick_model_result)
    gui.page.overlay.extend([pick_model_dialog])

    start_button = ft.ElevatedButton(
                "Start",
                icon =ft.icons.PLAY_CIRCLE,
                disabled =True,
                on_click = None,
            )
    stop_button = ft.ElevatedButton(
        "Stop",
        icon = ft.icons.STOP,
        visible = False,
        on_click = None,
    )


    progress_bar = ft.ProgressBar(value=0, width=180)
    progress_bar_text = ft.Text("Waiting for Input")
    segmentation_instance = segmentation(gui)

    def start_segmentation(e):
        print("start segmentation")
        start_button.visible = False
        stop_button.visible = True
        #progress_bar_text.value = "0%"
        model_text.disabled = True
        choose_model.disabled = True
        gui.page.update()
        segmentation_instance.run()
        #TODO what happens when segmentation is done

    def stop_segmentation(e):
        print("stop segmentation")
        start_button.visible = True
        stop_button.visible = False
        progress_bar_text.value = "Ready to Start"
        model_text.disabled = False
        choose_model.disabled = False
        gui.page.update()
        segmentation_instance.stop()

    start_button.on_click = start_segmentation
    stop_button.on_click = stop_segmentation

#brauchen hier listener um mit notifiern in segmentation.py zu interagieren
    def finished_segmentation():
        print("finished segmentation")
        progress_bar_text.value = "Finished"
        fl_button = Fluorescence().fluorescence_button
        fl_button.visible = True

        gui.page.update()
        #TODO fluoreszenz button soll on click die funktion starten

    def update_progress_bar(progress):
        print("update")
        progress_bar_text.value = progress
        gui.page.update()

    segmentation_instance.add_update_listener(listener=update_progress_bar)
    segmentation_instance.add_completion_listener(listener=finished_segmentation)

    pick_model_row = ft.Row(
        [
            progress_bar,
            progress_bar_text,
            start_button,
            stop_button
        ], alignment=ft.MainAxisAlignment.CENTER
    )

    model_text = ft.ListTile(
                                    leading=ft.Icon(name=ft.icons.COMPUTER_ROUNDED),
                                    title=ft.Text("Choose Model"),
                                )

    segmentation_container = ft.Container(
                        content=ft.Column(
                            [   model_text,
                                pick_model_row,
                            ]
                        )
                    )

    choose_model = ft.Container(
                        content=ft.IconButton(
                            icon=ft.icons.UPLOAD_FILE,
                            tooltip="Choose Model",
                            on_click=lambda _: pick_model_dialog.pick_files(allow_multiple=False),
                        ), alignment=ft.alignment.bottom_right,
                    )

    segmentation_card = ft.Card(
        content=ft.Container(
            content=ft.Stack(
                [   segmentation_container,
                    choose_model
                ]
            ),
            width=gui.page.width * (3 / 4),
            padding=10
        ),
    )
    return segmentation_card