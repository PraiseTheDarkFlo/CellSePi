import flet as ft

from cellsepi.expert_constants import ModuleType


class AddModule(ft.Container):
    """
    Class which handles the options in the right up corner in the GUI.
    """
    def __init__(self, builder):
        super().__init__()
        self.builder = builder
        self.pipeline_gui = builder.pipeline_gui
        self.page = builder.page
        self.menu_button = ft.PopupMenuButton(
            items=self.create_appbar_items(),
            content=ft.Icon(ft.Icons.ADD),
            tooltip="Add Module",
        )
        self.content = self.menu_button
        self.padding = 10
        self.alignment = ft.alignment.top_left


    def create_appbar_items(self):
        """
        Creates the appbar items that will be displayed in the GUI when the option button is clicked.
        """
        appbar_items = []
        for module_type in ModuleType:
            appbar_items.append(ft.PopupMenuItem(content=ft.Row([ft.IconButton(icon=ft.icons.BRIGHTNESS_1_ROUNDED,tooltip=module_type.value.gui_config().category.name, icon_color=module_type.value.gui_config().category.value), ft.Text(module_type.value.gui_config().name)]),
                                                 on_click=lambda e, mod_type = module_type: self.add_module(mod_type)))
        return appbar_items

    def add_module(self, module_type: ModuleType):
        self.pipeline_gui.add_module(module_type)
