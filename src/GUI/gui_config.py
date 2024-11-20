import flet as ft
from . import GUI

class GUIConfig:
    """
    Handles everything about the gui part of the config

    Attributes:
        config_class (ConfigFile): The config file.
        page (Page): The page to display in the GUI.
        name_items (List): A List of buttons/text fields for every profile to edit or select them.
        profile_chooser_overlay (CupertinoBottomSheet): The overlay that is opened when the profile name button is pressed to select profiles.
        profile_ref (Ref): The reference of the selected profile name button.
        txt_bf_ref (Ref): The reference of the bright field Textfield.
        txt_ms_ref (Ref): The reference of the mask suffix Textfield.
        txt_cp_ref (Ref): The reference of the channel prefix Textfield.
        txt_d_ref (Ref): The reference of the diameter Textfield.
    """
    def __init__(self,gui: GUI):
         self.config_class = gui.csp.config
         self.page = gui.page
         self.name_items = self.create_name_items_profiles()
         self.profile_chooser_overlay = self.create_profile_overlay()
         #--------------------------------
         #creates attributes to reference to the text boxes to changes their values or color etc...
         self.profile_ref = ft.Ref[ft.Text]()
         self.txt_bf_ref = ft.Ref[ft.Text]()
         self.txt_ms_ref = ft.Ref[ft.Text]()
         self.txt_cp_ref = ft.Ref[ft.Text]()
         self.txt_d_ref = ft.Ref[ft.Text]()

    def create_profile_overlay(self):
        """
        Creates the profile overlay.

        The overlay to choose or edit the profiles it pops up when the current profile is clicked on.

        Returns:
            Overlay (ft.CupertinoBottomSheet)
        """
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

    def calc_height(self):
        """
        Calculates the height of the list of profiles.

        Returns:
            calc (int): Returns the Calculation if it's smaller than 9.
            400 (int): If the profile count is greater than 8.
        """
        if len(self.config_class.config["Profiles"]) < 9:
            return 49 * len(self.config_class.config["Profiles"])
        else:
            return 400

    def text_field_activate(self,e, idx):
        """
        Handles the text field activation.

        Makes the textfield visible and the choose button invisible
        and makes sure that only one textfield is activ at a time.

        Args:
            e (Event): The event to handle.
            idx (int): The index of the profile to activate or deactivate the TextField.
        """
        if not self.name_items[idx]["textfield"].visible:
            self.name_items[idx]["textfield"].visible = True
            self.name_items[idx]["button"].visible = False
            for i in range(len(self.config_class.config["Profiles"])):
                if not i ==  idx:
                    self.name_items[i]["textfield"].visible = False
                    self.name_items[i]["button"].visible = True
            self.page.update()
        else:
            self.name_items[idx]["textfield"].visible = False
            self.name_items[idx]["button"].visible = True
            self.page.update()

    def text_field_written(self,e, idx):
        """
        Handles the text field written event.

        Args:
            e (Event): The event to handle.
            idx (int): The index of the profile to try to rename.
        """
        try:
            renamed = self.config_class.rename_profile(self.config_class.index_to_name(idx), e.control.value)
            if not renamed:
                self.page.snack_bar = ft.SnackBar(
                    ft.Text("The name is already taken!"))
                self.page.snack_bar.open = True
                self.page.update()
            else:
                self.name_items[idx]["textfield"].visible = False
                self.name_items[idx]["button"].visible = True
                self.name_items[idx]["textfield"].color = None
                self.profile_ref.current.value = self.config_class.get_selected_profile_name()
                self.update_overlay()
                self.page.update()
        except ValueError:
            self.page.snack_bar = ft.SnackBar(
                ft.Text("The name must be not empty!"))
            self.page.snack_bar.open = True
            self.page.update()

    def create_name_items_profiles(self):
        """
        Creates the TextField and Button items of a profile.
        """
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

    def selected_profile_changed(self,e, index):
        """
        Handles when a profile is selected and closes the overlay.

        Args:
            e (Event): The event to handle.
            index (int): The index of the selected profile.
        """
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

    def remove_profile(self,e, idx):
        """
        Handles the removing event of a profile.

        Args:
            e (Event): The event to handle.
            idx (int): The index of the profile that should be removed.
        """
        self.config_class.delete_profile(self.config_class.index_to_name(idx))
        self.profile_ref.current.value = self.config_class.get_selected_profile_name()
        self.update_overlay()
        self.page.update()

    def update_overlay(self):
        """
        Updates the overlay.

        The list needed to be rebuilt if the name of a profile is changed or a profile is deleted.
        """
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

    def create_list_items(self):
        """
        Creates the full List with the name_items and the buttons to trigger the event.

        The delete button is only added if the size of profiles is greater than 1.

        Returns:
            scroll List (List): the List of items for the profiles to change or selected them.
        """
        self.name_items = self.create_name_items_profiles()
        if len(self.config_class.config["Profiles"]) > 1:
            return [
                ft.Row(
                    controls=[
                        self.name_items[i]["textfield"],
                        self.name_items[i]["button"],
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
                        self.name_items[i]["textfield"],
                        self.name_items[i]["button"],
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


    def bf_updater(self, e):
        """
        Handles the bright field channel updating event.

        Checks if the value is valid.
        If it's not the methode creates a visible error for the user.

        Args:
            e (Event): The event to handle.
        """
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

    def ms_updater(self, e):
        """
        Handles the mask suffix updating event.

        Checks if the value is valid.
        If it's not the methode creates a visible error for the user.

        Args:
            e (Event): The event to handle.
        """
        if e.control.value:
            self.config_class.update_profile(self.config_class.get_selected_profile_name(), mask_suffix=e.control.value)
            self.txt_ms_ref.current.color = None
            self.page.update()
        else:
            self.page.snack_bar = ft.SnackBar(ft.Text("Mask suffix must be not empty!"))
            self.page.snack_bar.open = True
            self.txt_ms_ref.current.color = ft.colors.RED
            self.page.update()

    def cp_updater(self,e):
        """
        Handles the channel prefix updating event.

        Checks if the value is valid.
        If it's not the methode creates a visible error for the user.

        Args:
            e (Event): The event to handle.
        """
        if e.control.value:
            self.config_class.update_profile(self.config_class.get_selected_profile_name(), channel_prefix=e.control.value)
            self.txt_cp_ref.current.color = None
            self.page.update()
        else:
            self.page.snack_bar = ft.SnackBar(ft.Text("Channel prefix must be not empty!"))
            self.page.snack_bar.open = True
            self.txt_cp_ref.current.color = ft.colors.RED
            self.page.update()

    def d_updater(self,e):
        """
        Handles the diameter updating event.

        Checks if the value is valid.
        If it's not the methode creates a visible error for the user.

        Args:
            e (Event): The event to handle.
        """
        try:
            self.config_class.update_profile(self.config_class.get_selected_profile_name(), diameter=float(e.control.value))
            self.txt_d_ref.current.color = None
            self.page.update()
        except ValueError:
            self.page.snack_bar = ft.SnackBar(ft.Text("Diameter only allows decimals numbers, greater than 0"))
            self.page.snack_bar.open = True
            self.txt_d_ref.current.color = ft.colors.RED
            self.page.update()

    def create_profile_container(self):
        """
        Creates the profile container for the class GUI.

        Where you are able to choose the profile you want or change the attribute values
        of the profiles.
        Returns:
            profile container (Container)
        """
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
            label="Mask Suffix:",
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
