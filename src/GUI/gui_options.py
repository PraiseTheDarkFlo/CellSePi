import flet as ft

def switch(page: ft.Page):
    def toggle_theme(e):
        if theme_switch.value:
            page.theme_mode = ft.ThemeMode.DARK
        else:
            page.theme_mode = ft.ThemeMode.LIGHT
        page.update()

    theme_switch = ft.Switch(label="Darkmode", value=True)
    theme_switch.on_change = toggle_theme

    appbar_items = [
        ft.PopupMenuItem(text="Darkmode",
                         content= theme_switch)
    ]
    menu_button = ft.PopupMenuButton(
        items=appbar_items,
        content=ft.Icon(ft.icons.MENU),
        tooltip="Menu",

    )
    return ft.Container(
            content=menu_button,
            padding=10,
            alignment=ft.alignment.top_right
        )
