import os
import re
import flet as ft
from . import GUI
from ..fluorescence import Fluorescence
from .gui_fluorescence import fluorescence_button
from ..segmentation import segmentation
from ..notifier import Notifier
import src.GUI.gui_directory


def create_segmentation_card(gui: GUI):
    """
    This method creates a segmentation card for the GUI, which contains the progress bar and several buttons for
     controlling the run of the segmentation.

    Arguments:
         gui (GUI): the complete graphical user interface framework

    Returns:
        segmentation_card (ft.Card): the card containing all the elements needed to run the segmentation
    """
    # creating all the necessary buttons and their initial properties
    start_button = ft.ElevatedButton( # button to start the segmentation calculation
        text="Start",
        icon=ft.icons.PLAY_CIRCLE,
        tooltip="Start the segmentation",
        disabled=True,
        on_click=None
    )
    pause_button = ft.ElevatedButton( # button to pause the segmentation calculation while it is running
        text="Pause",
        icon=ft.icons.PAUSE_CIRCLE,
        visible=False,
        on_click=None,
    )
    cancel_button = ft.ElevatedButton( # button to completely cancel the currently running segmentation calculation
        text="Cancel",
        icon=ft.icons.CANCEL,
        visible=False,
        on_click=None,
        color=ft.Colors.RED
    )
    resume_button = ft.ElevatedButton( # button to resume the segmentation calculation after it has been paused
        text="Resume",
        icon=ft.icons.PLAY_CIRCLE,
        visible=False,
        on_click=None,
    )
    open_button = ft.IconButton(
        icon=ft.icons.OPEN_IN_NEW_ROUNDED,
        tooltip = "Open fluorescence file",
    )
    # button to start the fluorescence readout
    fluorescence = Fluorescence(gui.csp, gui)
    fl_button = fluorescence_button

    # progress bar, which is updated throughout the segmentation calculation and fluorescence readout
    progress_bar = ft.ProgressBar(value=0, width=180)
    progress_bar_text = ft.Text("Waiting for Input")
    segmentation_instance = segmentation(gui)

    # the following methods are called when clicking on the corresponding button
    def pick_model_result(e: ft.FilePickerResultEvent):
        """
        The result of the file selection is handled.

        Arguments:
            e (ft.FilePickerResultEvent): the result of the file picker event, i.e. the chosen file
        """
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

    def start_segmentation(e): # called when the start button is clicked
        """
        The start of the segmentation is initialized.
        """
        print("start segmentation")
        start_button.visible = False
        pause_button.visible = True
        cancel_button.visible = True
        model_text.disabled = True
        model_chooser.disabled = True
        fl_button.visible = False
        gui.page.update()
        segmentation_instance.run()

    def cancel_segmentation(e): # called when the cancel button is clicked
        """
        The running segmentation is cancelled and the masks calculated so far are deleted, i.e. return to the start state.
        """
        print("stop segmentation")
        #TODO hier muss ein notifier hin, der segmentation notified, dass die berechnung gestoppt werden soll
        #TODO in der Wartezeit soll klar sein, dass gerade gecancelt wird (weil es dauern könnte bis aktuelles Bild fertig bearbeitet wird)
        start_button.visible = True
        pause_button.visible = False
        cancel_button.visible = False
        progress_bar_text.value = "Ready to Start"
        model_text.disabled = False
        model_chooser.disabled = False
        gui.page.update()
        segmentation_instance.to_be_cancelled()

    def pause_segmentation(e): # called when the pause button is clicked
        """
        The running segmentation is paused and can be resumed again.
        """
        print("pause segmentation")
        segmentation_instance.to_be_paused()
        pause_button.visible = False
        resume_button.visible = True
        progress_bar_text.value = "Paused: " + progress_bar_text.value
        gui.page.update()

    def resume_segmentation(e): # called when the resume button is clicked
        """
        The segmentation is resumed again from the previously paused state.
        """
        print("resume segmentation")
        segmentation_instance.to_be_resumed()
        resume_button.visible = False
        pause_button.visible = True
        progress_words = progress_bar_text.value.split()
        progress_bar_text.value = progress_words[1] + progress_words[2] # remove "paused:" from string
        gui.page.update()

    start_button.on_click = start_segmentation
    cancel_button.on_click = cancel_segmentation
    pause_button.on_click = pause_segmentation
    resume_button.on_click = resume_segmentation

    def finished_segmentation():
        """
        This method updates the segmentation card when the segmentation is finished.
        """
        print("finished segmentation")
        progress_bar_text.value = "Finished"
        pause_button.visible = False
        cancel_button.visible = False
        fl_button.visible = True
        fl_button.disabled = False
        start_button.visible = True
        start_button.disabled = False
        model_text.disabled = False
        model_chooser.disabled = False
        print(gui.csp.mask_paths)

        gui.page.update()

    def update_progress_bar(progress,current_image):
        """
        This method updates the progress bar at any point before, during and after the segmentation and fluorescence process.

        Arguments:
            progress (int): the current progress
            current_image (int): the current image number
        """
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
            ft.Container(content=ft.Row([progress_bar, progress_bar_text])),
            ft.Container(content=ft.Row([start_button, pause_button, resume_button, cancel_button, fl_button, open_button]))
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

    model_chooser = ft.Container(
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
                    model_chooser
                ]
            ),
            padding=10
        ),
    )
    return segmentation_card,start_button