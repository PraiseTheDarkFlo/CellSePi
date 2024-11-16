import flet as ft
from . import GUI

#This class handles everything about the gui part of the config
class GUIConfig:
    def __init__(self,gui: GUI):
         self.config_class = gui.csp.config
         self.page = gui.page
         self.items = self.create_name_items_profiles()
         self.selected_profile_ref = ft.Ref[ft.Text]()
         self.profile_chooser_overlay = self.create_profile_overlay()
         #--------------------------------
         #creates attributes to reference to the text boxes to changes their values or color etc...
         self.profile_ref = ft.Ref[ft.Text]()
         self.txt_bf_ref = ft.Ref[ft.Text]()
         self.txt_ms_ref = ft.Ref[ft.Text]()
         self.txt_cp_ref = ft.Ref[ft.Text]()
         self.txt_d_ref = ft.Ref[ft.Text]()

    # creates the overlay to choose or edit the profiles it pops up when the current profile is clicked on
    def create_profile_overlay(self):
        return ft.CupertinoBottomSheet(
            content=ft.Column(
                [ft.ListView(
                    controls=self.create_list_items(),
                    height=self.calc_height(),
                    width=350,
                    auto_scroll=True,
                    spacing=10
                )],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            height=300,
            on_dismiss=lambda e: self.update_overlay(),
            padding=ft.padding.only(top=6),
        )

    #calculates the height of the list so the list is when it's less than 9
    #exaclty so big like the items
    def calc_height(self):
        if len(self.config_class.config["Profiles"]) < 9:
            return 49 * len(self.config_class.config["Profiles"])
        else:
            return 400

    #handels the event that the edit button is pressed
    #=> makes the textfield visible and the choose button invisible
    #and makes sure that only one textfield is activ at a time
    def text_field_activate(self,e, idx):
        if not self.items[idx]["textfield"].visible:
            self.items[idx]["textfield"].visible = True
            self.items[idx]["button"].visible = False
            for i in range(len(self.config_class.config["Profiles"])):
                if not i ==  idx:
                    self.items[i]["textfield"].visible = False
                    self.items[i]["button"].visible = True
            self.page.update()
        else:
            self.items[idx]["textfield"].visible = False
            self.items[idx]["button"].visible = True
            self.page.update()

    #handels the event that the text field of the profile has been updated
    def text_field_written(self,e, idx):
        try:
            renamed = self.config_class.rename_profile(self.config_class.index_to_name(idx), e.control.value)
            if not renamed:
                self.page.snack_bar = ft.SnackBar(
                    ft.Text("The name is already taken!"))
                self.page.snack_bar.open = True
                self.page.update()
            else:
                self.items[idx]["textfield"].visible = False
                self.items[idx]["button"].visible = True
                self.items[idx]["textfield"].color = None
                self.profile_ref.current.value = self.config_class.get_selected_profile_name()
                self.update_overlay()
                self.page.update()
        except ValueError:
            self.page.snack_bar = ft.SnackBar(
                ft.Text("The name must be not empty!"))
            self.page.snack_bar.open = True
            self.page.update()

    #creates the name items of the profiles so they can be selected and the name could be edited
    def create_name_items_profiles(self):
        return [
            {
                "textfield": ft.TextField(
                    value=profile,
                    width=200,
                    on_blur=lambda e,i=i:self.text_field_written(e,i),
                    visible = False,
                    border_color=ft.colors.BLUE_ACCENT,
                ),
                "button": ft.TextButton(
                    content=ft.Text(profile, size=20),
                    on_click=lambda e, i=i: self.selected_profile_changed(e, i),
                    width=200,
                    visible = True
                )
            }
            for i, profile in enumerate(self.config_class.config["Profiles"])
        ]

    #handels the event that a other profile has been selected and closes the overlay
    def selected_profile_changed(self,e, index):
        self.config_class.select_profile(self.config_class.index_to_name(index))
        self.profile_ref.current.value = self.config_class.get_selected_profile_name()
        self.txt_bf_ref.current.value = self.config_class.get_bf_channel()
        self.txt_ms_ref.current.value = self.config_class.get_mask_suffix()
        self.txt_cp_ref.current.value = self.config_class.get_channel_prefix()
        self.txt_d_ref.current.value = self.config_class.get_diameter()
        self.txt_bf_ref.current.color = None
        self.txt_ms_ref.current.color = None
        self.txt_cp_ref.current.color = None
        self.txt_d_ref.current.color = None
        self.page.close(self.profile_chooser_overlay)
        self.page.update()

    #handels the removing event of a profile when the button is pressed
    def remove_profile(self,e, idx):
        self.config_class.delete_profile(self.config_class.index_to_name(idx))
        self.profile_ref.current.value = self.config_class.get_selected_profile_name()
        self.update_overlay()
        self.page.update()

    #recreates the items for the list because they have changed
    def update_overlay(self):
        new_picker_items = self.create_list_items()
        new_content = ft.Column(
            controls=[
                ft.ListView(
                    controls=new_picker_items,
                    height=self.calc_height(),
                    width=350,
                    auto_scroll=True,
                    spacing=10
                )
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        )
        self.profile_chooser_overlay.content = new_content

    #creates the items for the list that is displayed in the overlay
    #and only adds the delete button if the profiles size is greater than 1
    def create_list_items(self):
        self.items = self.create_name_items_profiles()
        if len(self.config_class.config["Profiles"]) > 1:
            return [
                ft.Row(
                    controls=[
                        self.items[i]["textfield"],
                        self.items[i]["button"],
                        ft.IconButton(
                            icon=ft.icons.DELETE,
                            icon_color=ft.colors.RED,
                            on_click=lambda e, i=i: self.remove_profile(e, i),
                        ),
                        ft.IconButton(
                            icon=ft.icons.DRAW,
                            icon_color=ft.colors.BLUE,
                            on_click=lambda e, i=i: self.text_field_activate(e, i),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                )
                for i in range(len(self.config_class.config["Profiles"]))
            ]
        else:
            return [
                ft.Row(
                    controls=[
                        self.items[i]["textfield"],  # Verwende das gespeicherte TextField
                        self.items[i]["button"],  # Verwende das gespeicherte TextButton
                        ft.IconButton(
                            icon=ft.icons.DRAW,
                            icon_color=ft.colors.BLUE,
                            on_click=lambda e, i=i: self.text_field_activate(e, i),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                )
                for i in range(len(self.config_class.config["Profiles"]))
            ]


    #handels the update event of the Bright Field Channel and checks if the value is valid
    def bf_updater(self, e):
        try:
            self.config_class.update_profile(self.config_class.get_selected_profile_name(),
                                             bf_channel=int(e.control.value))
            self.txt_bf_ref.current.color = None
            self.page.update()
        except ValueError:
            self.page.snack_bar = ft.SnackBar(ft.Text("Bright field channel only allows counting numbers, greater than 0"))
            self.page.snack_bar.open = True
            self.txt_bf_ref.current.color = ft.colors.RED
            self.page.update()

    #handels the update event of the mask suffix and checks if the value is valid
    def ms_updater(self, e):
        if e.control.value:
            self.config_class.update_profile(self.config_class.get_selected_profile_name(), mask_suffix=e.control.value)
            self.txt_ms_ref.current.color = None
            self.page.update()
        else:
            self.page.snack_bar = ft.SnackBar(ft.Text("Mask suffix must be not empty!"))
            self.page.snack_bar.open = True
            self.txt_ms_ref.current.color = ft.colors.RED
            self.page.update()

    #handels the update event of the Channel Prefix and checks if the value is valid
    def cp_updater(self,e):
        if e.control.value:
            self.config_class.update_profile(self.config_class.get_selected_profile_name(), channel_prefix=e.control.value)
            self.txt_cp_ref.current.color = None
            self.page.update()
        else:
            self.page.snack_bar = ft.SnackBar(ft.Text("Channel prefix must be not empty!"))
            self.page.snack_bar.open = True
            self.txt_cp_ref.current.color = ft.colors.RED
            self.page.update()

    #handels the update event of the Diameter and checks if the value is valid
    def d_updater(self,e):
        try:
            self.config_class.update_profile(self.config_class.get_selected_profile_name(), diameter=float(e.control.value))
            self.txt_d_ref.current.color = None
            self.page.update()
        except ValueError:
            self.page.snack_bar = ft.SnackBar(ft.Text("Diameter only allows decimals numbers, greater than 0"))
            self.page.snack_bar.open = True
            self.txt_d_ref.current.color = ft.colors.RED
            self.page.update()

    #create the gui container where you can choose the profile and change the attribute values
    #of the profiles
    def create_gui_container(self):
        #--------------------------------------
        #creates the TextFields for the diffrent attributes of a profile
        tf_bf = ft.TextField(
            label="Bright Field Channel:",
            border_color=ft.colors.BLUE_ACCENT,
            value=self.config_class.get_bf_channel(),
            ref=self.txt_bf_ref,
            on_blur=lambda e: self.bf_updater(e),
            width=200,
            height=60,
        )

        tf_ms = ft.TextField(
            label="Masked Suffix:",
            border_color=ft.colors.BLUE_ACCENT,
            value=self.config_class.get_mask_suffix(),
            ref=self.txt_ms_ref,
            on_blur=lambda e: self.ms_updater(e),
            width=200,
            height=60,
        )

        tf_cp = ft.TextField(
            label="Channel Prefix:",
            border_color=ft.colors.BLUE_ACCENT,
            value=self.config_class.get_channel_prefix(),
            ref= self.txt_cp_ref,
            on_blur=lambda e: self.cp_updater(e),
            width=200,
            height=60,
        )

        tf_d = ft.TextField(
            label="Diameter:",
            border_color=ft.colors.BLUE_ACCENT,
            value=self.config_class.get_diameter(),
            ref=self.txt_d_ref,
            on_blur=lambda e: self.d_updater(e),
            keyboard_type=ft.KeyboardType.NUMBER,
            width=200,
            height=60,
        )



        #creates the Row with the current selected Profile as button and when you click on it,
        #it opens the profile_chooser_overlay
        profiles_row = ft.Row(
            tight=True,
            controls=[
                ft.Text("Profile:", size=23),
                ft.TextButton(
                    content=ft.Text(self.config_class.get_selected_profile_name(), size=23,ref=self.profile_ref),
                    style=ft.ButtonStyle(color=ft.colors.BLUE),
                    on_click=lambda e: e.control.page.open(
                        self.profile_chooser_overlay
                    ),
                ),
            ],
        )

        #creates the final Container that is displayed in the GUI
        return ft.Container(ft.Column([
                            profiles_row,
                            ft.Row([tf_bf, tf_cp]),
                            ft.Row([tf_ms, tf_d])]),padding=10)
