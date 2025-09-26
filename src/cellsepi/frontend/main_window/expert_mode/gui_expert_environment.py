import flet as ft
import asyncio

class ExpertEnvironment(ft.Container):
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
        self.switch_icon = ft.Icon(ft.Icons.REBASE_EDIT)
        self.button_expert_environment_menu = ft.PopupMenuButton(
            items=[self.button_event],
            content=self.switch_icon,
            tooltip="Expert Mode",
            on_open=lambda _: self.text.update(),
        )
        self.content = self.button_expert_environment_menu
        self.padding = 10
        self.alignment = ft.alignment.top_right
        self.old_view: (float, float,float) = (0.0, 0.0, 1.0)

    def change_environment(self, e):
        """
        Changing between modes.
        """
        if self.text.value == "Go To Expert Mode":
            self.go_to_expert_environment(e)
        else:
            self.old_view = self.gui.builder_environment.interactive_view.get_transformation_data()
            self.gui.ref_builder_environment.current.visible = False
            self.gui.ref_seg_environment.current.visible = True
            self.gui.ref_gallery_environment.current.visible = True
            self.page.title = "CellSePi"
            self.gui.page.update()
            self.text.value = "Go To Expert Mode"

    def go_to_expert_environment(self, e):
        """
        Switching to expert mode.
        """
        self.gui.ref_builder_environment.current.visible = True
        self.gui.ref_gallery_environment.current.visible = False
        self.gui.ref_training_environment.current.visible = False
        self.gui.ref_seg_environment.current.visible = False
        star = "*" if not self.gui.builder_environment.pipeline_storage.check_saved() else ""
        self.page.title = f"CellSePi - {self.gui.builder_environment.pipeline_gui.pipeline_name}{star}"
        self.gui.page.update()
        self.text.value = "Exit Expert Mode"
        self.gui.training_environment.text.value = "Go To Training"
        self.page.run_task(self._update_view)

    async def _update_view(self):
        """
        Loads the view of the expert environment, so its view has the orginal state when leaving the environment.
        """
        await asyncio.sleep(0.1)
        self.gui.builder_environment.interactive_view.set_transformation_data(self.old_view[0], self.old_view[1],self.old_view[2],300)
        self.gui.builder_environment.interactive_view.update()

