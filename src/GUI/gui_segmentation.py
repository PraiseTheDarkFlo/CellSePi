import os
import re
import flet as ft
from . import GUI
from ..fluorescence import Fluorescence
from .gui_fluorescence import fluorescence_button
from ..segmentation import segmentation
from ..notifier import Notifier
import src.GUI.gui_directory


#class gui_segmentation(GUI):

#build the segmentation_card with all events methods
def create_segmentation_card(gui: GUI):

    #method that does something with the result of the selection of the FIle
    def pick_model_result(e: ft.FilePickerResultEvent):
        if e.files is None:
            print("no model selected")
        elif e.files[0].path is not None:
            print("picked file")
            gui.csp.model_path = e.files[0].path
            progress_bar_text.value = "Ready to Start"
            start_button.disabled = False
            model_text.title.value = e.files[0].name
            gui.page.update()
            print("start_button is disabled", start_button.disabled)
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

    fluorescence = Fluorescence(gui.csp,gui)

    fl_button = fluorescence_button

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
        fl_button.visible = False
        gui.page.update()
        segmentation_instance.run()

    def stop_segmentation(e):
        print("stop segmentation")
        #TODO hier muss ein notifier hin, der segmentation notified, dass die berechnung gestoppt werden soll
        #TODO in der Wartezeit soll klar sein, dass gerade gecancelt wird (weil es dauern könnte bis aktuelles Bild fertig bearbeitet wird)
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
        stop_button.visible = False
        fl_button.visible = True
        fl_button.disabled = False
        start_button.visible = True
        start_button.disabled = False
        model_text.disabled = False
        choose_model.disabled = False

        gui.page.update()

    def update_progress_bar(progress,current_image):
        print("update")
        progress_bar_text.value = progress
        extracted_num = re.search(r'\d+', progress)
        if extracted_num is not None:
            progress_bar.value = int(extracted_num.group())/100
        gui.page.update()

#TODO wenn vorher schon masken vorhanden sind, dann sollen diese als backup gespeichert werden bevor die segmentierung startet und wenn der abbrechen button gedrückt wird sollen die alten wiederhergestellt werden
#TODO wenn neue files ausgewählt werden muss fluoreszenz button verschwinden
#TODO modell muss neu ausgewählt werden können
#TODO error anzeigen mit snack_bar (s.gui_config), z.B. wenn man starten will, ohne dass dateien ausgewählt sind
    # wenn image_path==none len(image_path)==0, dann start button nicht anzeigen
#TODO checken ob für alle bilder schon masken haben -> wenn ja, dann soll der fluoreszenz button schon erscheinen
    def fluorescence_readout(e):
        fluorescence.readout_fluorescence()
        fl_button.disabled = True
        start_button.disabled = True
        progress_bar_text.value = "Reading fluorescence"
        gui.page.update()

    def start_fl(e):
        progress_bar.value = 0
        progress_bar_text.value = "0 %"
        gui.page.update()

    def complete_fl():
        progress_bar.value = 0
        progress_bar_text.value = "Ready to start"
        gui.page.update()


    fl_button.on_click = fluorescence_readout
    fluorescence.add_start_listener(listener=start_fl)
    fluorescence.add_update_listener(listener=update_progress_bar)
    fluorescence.add_completion_listener(listener=complete_fl)
    segmentation_instance.add_update_listener(listener=update_progress_bar)
    segmentation_instance.add_completion_listener(listener=finished_segmentation)

    pick_model_row = ft.Row(
        [
            ft.Container(content=ft.Row([progress_bar,progress_bar_text])),
            ft.Container(content=ft.Row([start_button,stop_button,fl_button]))
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN
    )

    model_text = ft.ListTile(
                                    leading=ft.Icon(name=ft.icons.HUB_OUTLINED),
                                    title=ft.Text("Choose Model"),
                                )

    segmentation_container = ft.Container(
                        content=ft.Column(
                            [   model_text,
                                pick_model_row,
                            ]
                        )
                    )

    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    model_directory = os.path.join(project_root, "models")
    choose_model = ft.Container(
                        content=ft.IconButton(
                            icon=ft.icons.UPLOAD_FILE,
                            tooltip="Choose Model",
                            on_click=lambda _: pick_model_dialog.pick_files(allow_multiple=False, initial_directory=model_directory),
                        ), alignment=ft.alignment.bottom_right,
                    )

    segmentation_card = ft.Card(
        content=ft.Container(
            content=ft.Stack(
                [   segmentation_container,
                    choose_model
                ]
            ),
            padding=10
        ),
    )
    return segmentation_card