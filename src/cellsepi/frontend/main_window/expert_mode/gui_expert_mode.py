import flet as ft


class ExpertMode(ft.Container):

    def __init__(self, gui):
        super().__init__()
        self.gui = gui
        self.text = ft.Text("Go To Expert Mode")
        self.button_event = ft.PopupMenuItem(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.EXIT_TO_APP),
                    self.text
                ]
            ),
            on_click=lambda e: self.change_environment(e),
        )
        self.switch_icon = ft.Icon(ft.Icons.HANDYMAN)
        self.button_training_environment_menu = ft.PopupMenuButton(
            items=[self.button_event],
            content=self.switch_icon,
            tooltip="Expert Mode",
            on_open=lambda _: self.text.update(),
        )
        self.content = self.button_training_environment_menu
        self.padding = 10
        self.alignment = ft.alignment.top_right

    def change_environment(self, e):
        if self.text.value == "Go To Expert Mode":
            self.go_to_training_environment(e)
        else:
            self.gui.ref_training_environment.current.visible = False
            self.gui.ref_seg_environment.current.visible = True
            self.gui.page.update()
            self.text.value = "Go To Expert Mode"

    def go_to_training_environment(self, e):
        # delete the content of the page and reset the reference to the page (reference get sometimes lost)
        self.gui.ref_training_environment.current.visible = True
        self.gui.ref_seg_environment.current.visible = False
        self.gui.page.update()
        self.text.value = "Exit Expert Mode"
