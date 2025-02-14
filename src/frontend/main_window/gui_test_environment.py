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
import flet as ft
from cellpose import models, train, io
from cellpose.io import imread

class Testing(ft.Container):

    def __init__(self,gui):
        super().__init__()
        self.gui = gui
        self.text=ft.Text("Go To Training")
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
            on_open=lambda _: self.text.update(),
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
        self.weight=1e-4 #standard value for the weight

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
        self.train_loss= None
        self.test_loss = None


    def go_to_test_environment(self,e):
        #delete the content of the page and reset the reference to the page(reference get sometimes lost)
        self.gui.ref_test_environment.current.visible = True
        self.gui.ref_seg_environment.current.visible = False
        self.gui.page.update()
        self.text.value = "Exit Training"

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
        if self.text.value == "Go To Training":
            self.go_to_test_environment(e)

        else:
            self.gui.ref_test_environment.current.visible = False
            self.gui.ref_seg_environment.current.visible = True
            self.gui.page.update()
            self.text.value= "Go To Training"

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
            tooltip="Start the training epochs",
            disabled=False,
            on_click=self.start_training,
        )
        # progress bar, which is updated throughout the training periods


        progress_bar_text = ft.Text("Waiting for Input")
        text= ft.Text("Start Training")
        title = ft.ListTile(
            leading=ft.Icon(name=ft.icons.HUB_OUTLINED),
            title=text,
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
                [title,
                 pick_model_row,
                 ]
            )
        )

        progress_card = ft.Card(
            content=ft.Container(
                content=ft.Stack(
                    [test_container

                     ]
                ),
                padding=10
            ),
        )



        return progress_card



    def start_training(self,e):
        print("start")
        model = models.Cellpose(gpu=False, model_type=self.model)
        imgs = self.gui.directory.image_gallery
        #dont know if this is what is necessary: just something i found
        io.logger_setup()


        output = io.load_train_test_data(test_dir=self.gui.directory.directory_path,
                                         train_dir= self.gui.directory.directory_path,
                                         image_filter="",
                                         mask_filter="_seg.npy",
                                         look_one_level_down=False)


        images, labels, image_names, test_images, test_labels, image_names_test = output

        # e.g. retrain a Cellpose model
        model = models.CellposeModel(model_type=self.model)


        model_path, train_losses, test_losses = train.train_seg(model.net,
                                                                train_data=imgs,
                                                                train_labels=labels,
                                                                channels=[1, 2],
                                                                normalize=True,
                                                                test_data=test_images,
                                                                test_labels=test_labels,
                                                                weight_decay=self.weight,
                                                                SGD=True, #optimizing algo
                                                                learning_rate=self.learning_rate,
                                                                n_epochs=self.epochs,
                                                                batch_size=self.batch_size,
                                                                model_name="CP_new",
                                                                save_path=self.directory
                                                                )

       # self.test_loss= ft.Text(f"Test_Loss: -{train_losses}", size= 20)
       # self.test_loss = ft.Text(f"Training_Loss: -{test_losses}", size=20)
       # self.gui.page.update()





