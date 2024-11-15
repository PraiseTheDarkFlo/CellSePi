from pydoc import visiblename

import flet as ft
from . import GUI
from src import config_file
from ..custom_widgets_old import TextInput


class GUIConfig:
    def __init__(self,gui: GUI):
         self.config_class = gui.csp.config
         self.page = gui.page
         self.items = self.create_picker_items()
         self.selected_profile_ref = ft.Ref[ft.Text]()
         self.profile_ref = ft.Ref[ft.Text]()
         self.txt_bf_ref = ft.Ref[ft.Text]()
         self.txt_d_ref = ft.Ref[ft.Text]()
         self.txt_ms_ref = ft.Ref[ft.Text]()
         self.txt_cp_ref = ft.Ref[ft.Text]()
         self.overlay_picker = ft.CupertinoBottomSheet(
            content=ft.Column(
                [ft.ListView(
                    controls=self.get_picker_items(),
                    height=self.calc_height(),
                    width=350,
                    auto_scroll=True,
                    spacing=10
                )],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            height=300,
            on_dismiss=lambda e: self.reset_items(),
            padding=ft.padding.only(top=6),
        )
    def calc_height(self):
        if len(self.config_class.config["Profiles"]) < 9:
            return 49 * len(self.config_class.config["Profiles"])
        else:
            return 400

    def text_field_activate(self,e, idx):
        if not self.items[idx]["textfield"].visible:
            self.items[idx]["textfield"].visible = True
            self.items[idx]["button"].visible = False
            self.items[idx]["visible"] = False
            self.page.update()
        else:
            self.items[idx]["textfield"].visible = False
            self.items[idx]["button"].visible = True
            self.items[idx]["visible"] = True
            self.page.update()

    def reset_items(self):
       self.items = self.create_picker_items()
       self.update_overlay()

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
                self.items[idx]["visible"] = True
                self.items[idx]["textfield"].color = None
                self.profile_ref.current.value = self.config_class.get_selected_profile_name()
                self.update_overlay()
                self.page.update()
        except ValueError:
            self.page.snack_bar = ft.SnackBar(
                ft.Text("The name must be not empty!"))
            self.page.snack_bar.open = True
            self.page.update()


    def create_picker_items(self):
        return [
            {
                "textfield": ft.TextField(
                    value=profile,
                    width=200,
                    on_blur=lambda e,i=i:self.text_field_written(e,i),
                    visible=False,
                    border_color=ft.colors.BLUE_ACCENT,
                ),
                "button": ft.TextButton(
                    content=ft.Text(profile, size=20),
                    on_click=lambda e, i=i: self.handle_picker_change(e, i),
                    width=200,
                    visible=True,
                ),
                "visible": True  #TODO: DELETE
            }
            for i, profile in enumerate(self.config_class.config["Profiles"])
        ]

    def handle_picker_change(self,e, index):
        self.config_class.select_profile(self.config_class.index_to_name(index))
        self.profile_ref.current.value = self.config_class.get_selected_profile_name()
        self.txt_cp_ref.current.value = self.config_class.get_channel_prefix()
        self.txt_bf_ref.current.value = self.config_class.get_bf_channel()
        self.txt_ms_ref.current.value = self.config_class.get_mask_suffix()
        self.txt_d_ref.current.value = self.config_class.get_diameter()
        self.page.close(self.overlay_picker)
        self.page.update()

    def remove_profile(self,e, idx):
        self.config_class.delete_profile(self.config_class.index_to_name(idx))
        self.profile_ref.current.value = self.config_class.get_selected_profile_name()
        self.update_overlay()
        self.page.update()

    def update_overlay(self):
        new_picker_items = self.get_picker_items()
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
        self.overlay_picker.content = new_content

    def get_picker_items(self):
        self.items = self.create_picker_items()
        if len(self.config_class.config["Profiles"]) > 1:
            return [
                ft.Row(
                    controls=[
                        self.items[i]["textfield"],  # Verwende das gespeicherte TextField
                        self.items[i]["button"],  # Verwende das gespeicherte TextButton
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
    def cp_updater(self,e):
        self.config_class.update_profile(self.config_class.get_selected_profile_name(), channel_prefix=e.control.value)
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
    def ms_updater(self, e):
        #TODO: fix when felder empty sind
        self.config_class.update_profile(self.config_class.get_selected_profile_name(), mask_suffix=e.control.value)
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
    def create_gui_column(self):
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
        tf_ms = ft.TextField(
            label="Masked Suffix:",
            border_color=ft.colors.BLUE_ACCENT,
            value=self.config_class.get_mask_suffix(),
            ref=self.txt_ms_ref,
            on_blur=lambda e: self.ms_updater(e),
            width=200,
            height=60,
        )
        tf_bf = ft.TextField(
            label="Bright Field Channel:",
            border_color=ft.colors.BLUE_ACCENT,
            value=self.config_class.get_bf_channel(),
            ref=self.txt_bf_ref,
            on_blur=lambda e: self.bf_updater(e),
            width=200,
            height=60,
        )


        test = ft.Row(
            tight=True,
            controls=[
                ft.Text("Profile:", size=23),
                ft.TextButton(
                    content=ft.Text(self.config_class.get_selected_profile_name(), size=23,ref=self.profile_ref),
                    style=ft.ButtonStyle(color=ft.colors.BLUE),
                    on_click=lambda e: e.control.page.open(
                        self.overlay_picker
                    ),
                ),
            ],
        )

        return ft.Column([ft.Row([test
                                  ]),
                          ft.Row([tf_bf, tf_cp]),
                          ft.Row([tf_ms, tf_d])])
