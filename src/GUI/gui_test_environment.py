#the following parameter need to be included/adaptable :
# modeltype: 'cyto','nuclei' or user difiend
#batch size
#epochs
#learning rate
#vortrainiert oder out of scratch (boolean)
#optimierungsalgo
#diameter
#Schichten im Modell
#directory
#
from cProfile import label

from . import GUI
import flet as ft
import os

class Testing(ft.Container):

    def __init__(self,gui:GUI):
        super().__init__()
        self.gui = gui
        self.text=ft.Text("Go To Testing")
        self.button_event= ft.PopupMenuItem(
                content = ft.Row(
            [
                ft.Icon(ft.Icons.EXIT_TO_APP),
                self.text,
            ]
        ),
        on_click = lambda e: self.change_environment(e),
        )
        self.button_test_environment_menu=ft.PopupMenuButton(
            items= [self.button_event],
            content=ft.Icon(ft.icons.MODEL_TRAINING),
        )
        self.content = self.button_test_environment_menu
        self.padding = 10
        self.alignment = ft.alignment.top_right

        self.model=None
        self.batch_size=None
        self.epochs=None
        self.learning_rate=None
        self.pre_trained=None
        self.diameter=self.gui.csp.config.get_diameter()
        self.directory= r"...\CellSePi\models"
        self.weight=1e-4

        self.color = ft.colors.BLUE_400

        self.field_model=ft.TextField(label="modeltype", value=self.model, border_color=self.color,
                     on_change=lambda e: self.changed_input("modeltype",e))
        self.field_batch=ft.TextField(label="batch_size", value=self.batch_size, border_color=self.color,
                     on_change=lambda e: self.changed_input("batch_size",e) )
        self.field_epoch=ft.TextField(label="epochs", value=self.epochs, border_color=self.color,
                     on_change=lambda e: self.changed_input("epochs",e))
        self.field_lr=ft.TextField(label="learning_rate", value=self.learning_rate, border_color=self.color,
                     on_change=lambda e: self.changed_input("learning_rate",e))
        self.field_trained=ft.TextField(label="pre_trained", value=self.pre_trained, border_color=self.color,
                     on_change=lambda e: self.changed_input("pre_trained",e))
        self.field_diameter=ft.TextField(label="diameter", value=self.diameter, border_color=self.color,
                     on_change=lambda e: self.changed_input("diameter",e))
        self.field_weights = ft.TextField(label="weight", value=self.weight, border_color=self.color,
                                        on_change=lambda e: self.changed_input("weight", e))
        self.field_directory = ft.TextField(label="directory", value=self.directory, border_color=self.color,
                                           read_only=True)

        self.progress_bar = ft.ProgressBar(value=0, width=180)



    def go_to_test_environment(self,e):
        self.text.value= "Exit Testing"
        container= self.add_parameter_container()
        card= self.create_testing_card()
        #delete the content of the page and reset the reference to the page(reference get sometimes lost)
        page = self.gui.page
        self.gui.page.clean()
        self.gui.page = page

        self.gui.page.add(
            ft.Column(
                [
                    ft.Row(
                        [
                            # LEFT COLUMN that handles all elements on the left side(canvas,switch_mask,segmentation)
                            ft.Column(
                                [
                                    container,
                                    card,
                                ],
                                expand=True,
                                alignment=ft.MainAxisAlignment.START,
                            ),
                            # RIGHT COLUMN that handles gallery and directory_card
                            ft.Column(
                                [
                                    self.gui.directory,
                                    ft.Card(
                                        content=ft.Stack(
                                            [ft.Container(self.gui.progress_ring, alignment=ft.alignment.center),
                                             ft.Container(self.gui.directory.image_gallery, padding=20)]),
                                        expand=True
                                    ),
                                ],
                                expand=True,
                            ),
                            ft.Column([self.gui.op, self.gui.test_environment]),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        expand=True,
                    ),
                ],
                expand=True
            )
        )
        self.gui.page.update()

    def add_parameter_container(self):

        return ft.Container(
            ft.Column(
                [ self.field_model, self.field_batch, self.field_epoch,self.field_weights, self.field_lr, self.field_trained,self.field_diameter, self.field_directory

            ]
        ), padding= 10,

    )



    def changed_input(self,field, e):
        updated_value= e.control.value

        if field == "modeltype":
            self.model=updated_value
            self.field_model.value =updated_value
        elif field == "batch_size":
            self.batch_size = updated_value
            self.field_batch.value= updated_value
        elif field == "epochs":
            self.epochs = updated_value
            self.field_epoch= updated_value
        elif field == "learning_rate":
            self.learning_rate = updated_value
            self.field_lr= updated_value
        elif field == "pre_trained":
            self.pre_trained = updated_value
            self.field_trained.value= updated_value
        elif field == "weight":
            self.weight= updated_value
            self.field_weights=updated_value
        else:
            self.diameter = updated_value
            self.field_diameter.value= updated_value

        self.gui.page.update()



    def change_environment(self,e):
        if self.text.value == "Go To Testing":
            self.go_to_test_environment(e)

        else:
            self.text.value= "Go To Testing"
            page = self.gui.page
            self.gui.page.clean()
            self.gui.page = page
            self.gui.build()

    def create_testing_card(self):
        """
        This method creates a card for the GUI, which contains the progress bar and several buttons for
         controlling the run of the testing.

        Returns:
            testing_card (ft.Card): the card containing all the elements needed to run the testing
        """

        start_button = ft.ElevatedButton(
            text="Start",
            icon=ft.icons.PLAY_CIRCLE,
            tooltip="Start the testing epochs",
            disabled=False,
            on_click=self.start_training
        )
        # progress bar, which is updated throughout the training periods


        progress_bar_text = ft.Text("Waiting for Input")
        model_text= ft.Text("Choose Model")
        model_title = ft.ListTile(
            leading=ft.Icon(name=ft.icons.HUB_OUTLINED),
            title=model_text,
        )
        pick_model_row = ft.Row(
            [
                ft.Container(content=ft.Row([self.progress_bar, progress_bar_text])),
                ft.Container(
                    content=ft.Row([start_button]))
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )
        test_container = ft.Container(
            content=ft.Column(
                [model_title,
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
                on_click=lambda _: pick_model_dialog.pick_files(allow_multiple=False,
                                                                initial_directory=model_directory),
            ), alignment=ft.alignment.bottom_right,
        )
        progress_card = ft.Card(
            content=ft.Container(
                content=ft.Stack(
                    [test_container,
                     model_chooser
                     ]
                ),
                padding=10
            ),
        )


        def pick_model_result(e: ft.FilePickerResultEvent):
            """
            The result of the file selection is handled.

            Arguments:
                e (ft.FilePickerResultEvent): the result of the file picker event, i.e. the chosen file
            """
            if e.files is None:
                print("no model selected")
            elif e.files[0].path is not None:
                if self.gui.ready_to_start:
                    progress_bar_text.value = "Ready to Start"
                    start_button.disabled = False
                model_text.value = e.files[0].name
                model_text.color = None
                self.gui.csp.model_path = e.files[0].path
                self.gui.page.update()
            else:
                print("no model selected")

        pick_model_dialog = ft.FilePicker(on_result=pick_model_result)
        self.gui.page.overlay.extend([pick_model_dialog])

        return progress_card



    def start_training(self):
        print("start")


