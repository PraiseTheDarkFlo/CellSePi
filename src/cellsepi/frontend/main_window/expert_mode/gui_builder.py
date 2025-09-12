from pathlib import Path

from flet_core.colors import WHITE60
from flet_extended_interactive_viewer import FletExtendedInteractiveViewer

from cellsepi.frontend.main_window.expert_mode.gui_pipeline import PipelineGUI
from cellsepi.frontend.main_window.expert_mode.expert_constants import *
from cellsepi.frontend.main_window.expert_mode.gui_pipeline_listener import PipelineChangeListener, ModuleExecutedListener, ModuleStartedListener, \
    ModuleProgressListener, ModuleErrorListener, DragAndDropListener
from cellsepi.backend.main_window.expert_mode.pipeline_storage import PipelineStorage

class Builder:
    def __init__(self,page: ft.Page):
        self.page = page
        self.builder_page_stack = None
        self.pipeline_gui = PipelineGUI(page)
        self.pipeline_gui.interactive_view = None
        self.pipeline_running_event = None
        self.help_text =  ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "Move Modules",
                        size=50,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.GREY_500
                    ),
                    ft.Row([
                        ft.Text(
                            "here",
                            size=40,
                            italic=True,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.GREY_400
                        ),
                        ft.Icon(ft.Icons.CROP_FREE,size=50,color=ft.Colors.GREY_400), #Icons.COPY_ALL_ROUNDED,CONTROL_CAMERA,Icons.CROP_FREE, Icons.VIEW_IN_AR,Icons.HIGHLIGHT_ALT_ROUNDED
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    ),
                ],
                spacing=2,
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
            ,alignment=ft.alignment.center,
            width=self.page.width,
            height=self.page.height,
            animate_opacity= ft.Animation(duration=600, curve=ft.AnimationCurve.LINEAR_TO_EASE_OUT),
        )
        self.pipeline_storage = PipelineStorage(self.pipeline_gui)
        self.file_picker = ft.FilePicker(
            on_result=lambda a: self.on_select_file(a))
        self.file_saver = ft.FilePicker(
            on_result=lambda a: self.on_file_saved(a))
        self.page.overlay.extend([self.file_picker,self.file_saver])
        self.load_button = ft.IconButton(icon=ft.Icons.UPLOAD_FILE, on_click=lambda e: self.click_load_file(),
                                         icon_color=WHITE60,
                                         style=ft.ButtonStyle(
                                             shape=ft.RoundedRectangleBorder(radius=12), ),
                                         tooltip="Load pipeline\n[Ctrl + L]", hover_color=ft.Colors.WHITE12)
        self.save_as_button = ft.IconButton(icon=ft.Icons.SAVE_AS_ROUNDED, on_click=lambda e: self.click_save_as_file(),
                                            icon_color=WHITE60 if len(self.pipeline_gui.modules) > 0 else ft.Colors.WHITE24, disabled=False if len(self.pipeline_gui.modules) > 0 else True,
                                            style=ft.ButtonStyle(
                                               shape=ft.RoundedRectangleBorder(radius=12), ),
                                            tooltip="Save as pipeline\n[Ctrl + Shift + S]", hover_color=ft.Colors.WHITE12)

        def on_keyboard(e: ft.KeyboardEvent):
            if e.shift and e.ctrl and e.key == "S" and not e.alt and not e.meta:
                if not self.save_as_button.disabled:
                    self.click_save_as_file()
            if e.ctrl and e.key == "S" and not e.alt and not e.shift and not e.meta:
                if not self.save_button.disabled:
                    self.click_save_file()
            if e.ctrl and e.key == "L" and not e.alt and not e.shift and not e.meta:
                if not self.load_button.disabled:
                    self.click_load_file()
            if e.ctrl and e.key == "R" and not e.alt and not e.shift and not e.meta:
                self.run_menu_click()
            if e.ctrl and e.key == "D" and not e.alt and not e.shift and not e.meta:
                self.delete_button_click()
            if e.ctrl and e.key == "P" and not e.alt and not e.shift and not e.meta:
                self.port_button_click()
            if e.ctrl and e.key == "Q" and not e.alt and not e.shift and not e.meta:
                if not self.page_backward.disabled:
                    self.press_page_backward()
            if e.ctrl and e.key == "E" and not e.alt and not e.shift and not e.meta:
                if not self.page_forward.disabled:
                    self.press_page_forward()
            if e.ctrl and e.key == "Z" and not e.alt and not e.shift and not e.meta:
                self.zoom_menu_click()
            if e.ctrl and e.key == "." and not e.alt and not e.shift and not e.meta:
                self.interactive_view.zoom(1.0+ZOOM_VALUE)
            if e.ctrl and e.key == "," and not e.alt and not e.shift and not e.meta:
                self.interactive_view.zoom(1.0-ZOOM_VALUE)
            if e.ctrl and e.key == "-" and not e.alt and not e.shift and not e.meta:
                self.interactive_view.reset(400)

        self.page.on_keyboard_event = on_keyboard
        self.save_button = ft.IconButton(icon=ft.Icons.SAVE_ROUNDED, on_click=lambda e: self.click_save_file(),
                                            icon_color=WHITE60 if self.pipeline_gui.pipeline_directory != "" else ft.Colors.WHITE24,
                                            disabled=False if self.pipeline_gui.pipeline_directory != "" else True,
                                            style=ft.ButtonStyle(
                                             shape=ft.RoundedRectangleBorder(radius=12), ),
                                            tooltip="Save pipeline\n[Ctrl + S]", hover_color=ft.Colors.WHITE12)
        self.run_menu_button = ft.IconButton(icon=ft.Icons.PLAY_ARROW, on_click=lambda e: self.run_menu_click(),
                                         icon_color=WHITE60,
                                         style=ft.ButtonStyle(
                                             shape=ft.RoundedRectangleBorder(radius=12), ),
                                         tooltip="Show run menu\n[Ctrl + R]", hover_color=ft.Colors.WHITE12)
        self.delete_button = ft.IconButton(icon=ft.Icons.DELETE,on_click=lambda e: self.delete_button_click(),icon_color=WHITE60,
                                                 style=ft.ButtonStyle(
                                              shape=ft.RoundedRectangleBorder(radius=12),),
                                                 tooltip="Show delete buttons\n[Ctrl + D]", hover_color=ft.Colors.WHITE12)
        self.port_button = ft.IconButton(icon=ft.Icons.VISIBILITY, on_click=lambda e: self.port_button_click(),
                                           icon_color=WHITE60,
                                           style=ft.ButtonStyle(
                                               shape=ft.RoundedRectangleBorder(radius=12), ),
                                           tooltip="Show which ports get transferred\n[Ctrl + P]", hover_color=ft.Colors.WHITE12)

        self.slider_horizontal = ft.Slider(min=0,max=1,height=40,on_change=lambda e: self.scroll_horizontal(e),active_color=ft.Colors.BLUE_400,inactive_color=WHITE60,overlay_color=ft.Colors.WHITE12)
        self.left_tools = ft.Container(ft.Container(ft.Column(
                [
                    self.load_button, self.save_as_button,self.save_button,self.run_menu_button,self.delete_button,self.port_button
                ], tight=True,spacing=2
            ), bgcolor=MENU_COLOR, expand=True
            ),bgcolor=ft.Colors.TRANSPARENT,border_radius=ft.border_radius.all(10),
            bottom=40,left=SPACING_X,width=40,blur=10)


        self.start_button = ft.ElevatedButton(  # button to start the pipeline
            text="Start",
            icon=ft.Icons.PLAY_CIRCLE,
            tooltip="Start the pipeline",
            disabled=False if len(self.pipeline_gui.modules) > 0 else True,
            on_click=lambda e:self.run(),
            opacity=0.75,
        )
        self.resume_button = ft.ElevatedButton(  # button to resume the pipeline
            text="Resume the pipeline",
            icon=ft.Icons.PLAY_CIRCLE,
            visible=False,
            on_click=self.pipeline_gui.pipeline.run(resume=True),
            opacity=0.75
        )
        self.progress_bar_module = ft.ProgressBar(value=0, width=220,bgcolor=ft.Colors.WHITE24,color=ft.Colors.BLUE_400)
        self.progress_pipeline = ft.ProgressRing(value=0,width=50,height=50,stroke_width=8,bgcolor=ft.Colors.WHITE24,color=ft.Colors.BLUE_400)
        self.progress_text = ft.Text(f"{self.pipeline_gui.modules_executed}/{len(self.pipeline_gui.pipeline.modules)}",weight=ft.FontWeight.BOLD,tooltip="How many modules has been executed",color=ft.Colors.WHITE60)
        self.progress_stack = ft.Stack([self.progress_pipeline,ft.Container(self.progress_text,alignment=ft.alignment.center)],width=50,height=50,)
        self.progress_bar_module_text = ft.Text("0%",color=ft.Colors.WHITE60)
        self.progress_and_start = ft.Column([ft.Container(self.progress_stack,alignment=ft.alignment.center),
            ft.Container(
                content=ft.Stack([self.start_button, self.resume_button]),alignment=ft.alignment.center)],width=85,spacing=20
        )
        self.running_module = ft.Text("Module",color=ft.Colors.WHITE70,width=230,overflow=ft.TextOverflow.ELLIPSIS,max_lines=1,style=ft.TextThemeStyle.HEADLINE_SMALL)
        self.info_text = ft.Text("Idle, waiting for start.",color=ft.Colors.WHITE60,width=250,overflow=ft.TextOverflow.ELLIPSIS,max_lines=2)
        self.category_icon = ft.Icon(ft.Icons.CATEGORY_ROUNDED,color=ft.Colors.GREEN)
        self.run_infos = ft.Column([ft.Row([self.category_icon,self.running_module]),self.info_text])
        self.left_run_menu = ft.Column([
            self.run_infos,ft.Row([ft.Container(self.progress_bar_module),self.progress_bar_module_text],width=260),
        ],alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        self.zoom_menu_button = ft.IconButton(icon=ft.Icons.SEARCH, on_click=lambda e: self.zoom_menu_click(),
                                             icon_color=WHITE60,
                                             style=ft.ButtonStyle(
                                                 shape=ft.RoundedRectangleBorder(radius=12), ),
                                             tooltip="Show zoom menu\n[Ctrl + Z]", hover_color=ft.Colors.WHITE12)



        self.right_tools = ft.Container(ft.Container(ft.Column(
            [
                self.zoom_menu_button,
            ], tight=True, spacing=2
        ), bgcolor=MENU_COLOR, expand=True
        ), bgcolor=ft.Colors.TRANSPARENT, border_radius=ft.border_radius.all(10),
            bottom=40, right=SPACING_X, width=40, blur=10)

        self.interactive_view = None
        self.zoom_menu = ft.Container(ft.Container(ft.Row(
            [
                ft.IconButton(icon=ft.Icons.ZOOM_IN, icon_color=WHITE60,
                                             style=ft.ButtonStyle(
                                                 shape=ft.RoundedRectangleBorder(radius=12), ), on_click=lambda e: self.interactive_view.zoom(1.0+ZOOM_VALUE),tooltip="Zoom in\n[Ctrl + .]",),
                ft.IconButton(icon=ft.Icons.ZOOM_OUT, icon_color=WHITE60,
                                             style=ft.ButtonStyle(
                                                 shape=ft.RoundedRectangleBorder(radius=12), ), on_click=lambda e: self.interactive_view.zoom(1.0-ZOOM_VALUE),tooltip="Zoom out\n[Ctrl + ,]",),
                ft.IconButton(icon=ft.Icons.CROP_FREE, icon_color=WHITE60,
                           style=ft.ButtonStyle(
                               shape=ft.RoundedRectangleBorder(radius=12), ),
                           on_click=lambda e: self.interactive_view.reset(400),tooltip="Reset view\n[Ctrl + -]",),
            ], spacing=2
        ), bgcolor=MENU_COLOR, expand=True
        ), bgcolor=ft.Colors.TRANSPARENT, border_radius=ft.border_radius.all(10),
            bottom=40, right=self.right_tools.right + self.right_tools.width + 5, blur=10, opacity=0,
            animate_opacity=ft.Animation(duration=300, curve=ft.AnimationCurve.LINEAR_TO_EASE_OUT),
            animate=ft.Animation(duration=300, curve=ft.AnimationCurve.LINEAR_TO_EASE_OUT),
        )

        self.run_menu = ft.Container(ft.Container(ft.Row(
            [
                ft.Container(self.left_run_menu,padding=10),ft.VerticalDivider(), ft.Column([ft.Row([ft.Container(self.progress_and_start,padding=10)],alignment=ft.MainAxisAlignment.CENTER)],alignment=ft.MainAxisAlignment.CENTER),
            ], spacing=2
        ), bgcolor=MENU_COLOR, expand=True, padding=10
        ), bgcolor=ft.Colors.TRANSPARENT, border_radius=ft.border_radius.all(10),width=0,height=150,
            bottom=40, left=self.left_tools.left + self.left_tools.width + 5,blur=10,opacity=0,
            animate_opacity=ft.Animation(duration=300, curve=ft.AnimationCurve.LINEAR_TO_EASE_OUT),
            animate=ft.Animation(duration=300, curve=ft.AnimationCurve.LINEAR_TO_EASE_OUT),
            )
        self.scroll_horizontal_row = None
        self.work_area = None
        self.setup()
        self.page_forward = ft.IconButton(icon=ft.Icons.CHEVRON_RIGHT_SHARP, on_click=lambda e: self.press_page_forward(),
                                          icon_color=ft.Colors.WHITE60,
                                          style=ft.ButtonStyle(
                                         shape=ft.RoundedRectangleBorder(radius=12), ),
                                          visible=True if self.pipeline_gui.show_room_max_page_number != 1 else False,
                                          tooltip="Get to the next page\n[Ctrl + E]", hover_color=ft.Colors.WHITE12)
        self.page_backward = ft.IconButton(icon=ft.Icons.CHEVRON_LEFT_SHARP, on_click=lambda e: self.press_page_backward(),
                                           icon_color=ft.Colors.WHITE24,
                                           style=ft.ButtonStyle(
                                           shape=ft.RoundedRectangleBorder(radius=12), ), disabled=True,
                                           tooltip="Return to the last page\n[Ctrl + Q]", hover_color=ft.Colors.WHITE12, visible=True if self.pipeline_gui.show_room_max_page_number != 1 else False)
        self.pipeline_gui.build_show_room(self.builder_page_stack)
        self.pipeline_gui.interactive_view = self.interactive_view
        self.switch_pages = ft.Container(ft.Container(ft.Row(
                    [
                        self.page_backward, self.page_forward,
                    ], tight=True,spacing=2
                ), bgcolor=MENU_COLOR, expand=True, height=40
                ), bgcolor=ft.Colors.TRANSPARENT, border_radius=ft.border_radius.all(10),
                    top=self.pipeline_gui.show_room_container.top + self.pipeline_gui.show_room_container.height + 5,
                    left=self.pipeline_gui.show_room_container.left,blur=10)
        self.builder_page_stack.controls.insert(2, self.switch_pages)
        self.add_all_listeners()

    def run(self,ignore_check=False):
        show_room_names = [m.name for m in self.pipeline_gui.show_room_modules]
        if not ignore_check and not self.pipeline_gui.pipeline.check_pipeline_runnable(show_room_names):
            def dismiss_dialog(e):
                cupertino_alert_dialog.open = False
                e.control.page.update()
                for mod in self.pipeline_gui.modules.values():
                    if not self.pipeline_gui.pipeline.check_module_satisfied(mod.name):
                        if not mod.show_ports:
                            mod.ports_in_out_clicked()
            def dismiss_dialog_ignore(e):
                cupertino_alert_dialog.open = False
                e.control.page.update()
                self.run(True)
            cupertino_alert_dialog = ft.CupertinoAlertDialog(
                title=ft.Text("Mandatory Input Warning"),
                content=ft.Text("Not all mandatory inputs are satisfied."),
                actions=[
                    ft.CupertinoDialogAction(
                        "Change modules",is_default_action=True, on_click=dismiss_dialog
                    ),
                    ft.CupertinoDialogAction(text="Skip modules", is_destructive_action=True, on_click=dismiss_dialog_ignore),
                ],
            )
            self.page.overlay.append(cupertino_alert_dialog)
            cupertino_alert_dialog.open = True
            self.page.update()
            return
        self.info_text.spans = []
        self.info_text.value = "Idle, waiting for start."
        self.info_text.update()
        self.start_button.disabled = True
        self.start_button.update()
        self.load_button.disabled = True
        self.load_button.icon_color = ft.Colors.WHITE24
        self.load_button.update()
        for module in self.pipeline_gui.modules.values():
            self.pipeline_gui.lines_gui.update_delete_buttons(module,True)
            module.waiting_button.visible = True
            module.start_button.visible = False
            module.delete_button.visible = False
            module.waiting_button.update()
            module.start_button.update()
            module.delete_button.update()
            module.disable_tools()
            module.error_stack.visible = False
            module.error_stack.update()
            module.check_warning()

        self.pipeline_gui.pipeline.run(show_room_names)
        self.pipeline_gui.modules_executed = 0
        self.update_modules_executed()
        self.start_button.disabled = False
        self.start_button.update()
        self.load_button.disabled = False
        self.load_button.icon_color = ft.Colors.WHITE60
        self.load_button.update()
        if self.pipeline_running_event is not None:
            self.pipeline_running_event.set()

    def add_all_listeners(self):
        pipeline_change_listener = PipelineChangeListener(self)
        self.pipeline_gui.pipeline.event_manager.subscribe(listener=pipeline_change_listener)
        module_executed_listener =ModuleExecutedListener(self)
        self.pipeline_gui.pipeline.event_manager.subscribe(listener=module_executed_listener)
        module_started_listener =ModuleStartedListener(self)
        self.pipeline_gui.pipeline.event_manager.subscribe(listener=module_started_listener)
        module_progress_listener =ModuleProgressListener(self)
        self.pipeline_gui.pipeline.event_manager.subscribe(listener=module_progress_listener)
        module_error_listener =ModuleErrorListener(self)
        self.pipeline_gui.pipeline.event_manager.subscribe(listener=module_error_listener)
        drag_and_drop_listener =DragAndDropListener(self)
        self.pipeline_gui.pipeline.event_manager.subscribe(listener=drag_and_drop_listener)

    def update_modules_executed(self):
        current =self.pipeline_gui.modules_executed
        if not self.pipeline_gui.pipeline.running:
            total = len(self.pipeline_gui.pipeline.modules) - len(ModuleType) * 2
            self.progress_pipeline.value = (current / total) if total > 0 else 0
            self.pipeline_gui.module_running_count = total
            self.progress_text.value = f"{current}/{total}"
        else:
            self.progress_pipeline.value = (current / self.pipeline_gui.module_running_count) if self.pipeline_gui.module_running_count > 0 else 0
            self.progress_text.value = f"{current}/{self.pipeline_gui.module_running_count}"
        self.progress_text.update()
        self.page.update()

    def click_load_file(self):
        self.file_picker.pick_files(file_type=ft.FilePickerFileType.CUSTOM, allowed_extensions=["csp"],
                                    allow_multiple=False)
        self.load_button.icon_color = ft.Colors.BLUE_400
        self.load_button.update()

    def click_save_as_file(self):
        self.file_saver.save_file(file_type=ft.FilePickerFileType.CUSTOM, allowed_extensions=["csp"],
                             dialog_title="Save Pipeline", file_name=self.pipeline_gui.pipeline_name,
                             initial_directory=self.pipeline_gui.pipeline_directory)
        self.save_as_button.icon_color = ft.Colors.BLUE_400
        self.save_as_button.update()

    def click_save_file(self):
        self.save_button.icon_color = ft.Colors.BLUE_400
        self.save_button.update()
        path = self.pipeline_storage.save_pipeline()
        self.pipeline_gui.page.open(
            ft.SnackBar(ft.Text(f"Pipeline saved at {path}", color=ft.Colors.WHITE), bgcolor=ft.Colors.GREEN))
        self.pipeline_gui.page.update()

        self.page.title = f"CellSePi - {self.pipeline_gui.pipeline_name}"
        self.save_button.icon_color = ft.Colors.WHITE24
        self.save_button.disabled = True
        self.page.update()

    def on_select_file(self, e):
        """
        Handles if a file is selected.
        """
        if e.files is not None:
            if not self.pipeline_storage.check_saved():
                def cancel_dialog(a):
                    cupertino_alert_dialog.open = False
                    a.control.page.update()

                def ok_dialog(a):
                    cupertino_alert_dialog.open = False
                    a.control.page.update()
                    if self.pipeline_gui.pipeline.running:
                        self.pipeline_gui.page.open(
                            ft.SnackBar(
                                ft.Text(f"Failed to load pipeline: a previous pipeline execution is still active!",
                                        color=ft.Colors.WHITE),
                                bgcolor=ft.Colors.RED))
                        self.pipeline_gui.page.update()
                        return
                    self.pipeline_storage.load_pipeline(e.files[0].path)

                cupertino_alert_dialog = ft.CupertinoAlertDialog(
                    title=ft.Text("Unsaved Changes"),
                    content=ft.Text("Loading will overwrite the currently opened pipeline."),
                    actions=[
                        ft.CupertinoDialogAction(
                            "Cancel",is_default_action=True, on_click=cancel_dialog
                        ),
                        ft.CupertinoDialogAction(text="Ok", is_destructive_action=True, on_click=ok_dialog),
                    ],
                )
                self.page.overlay.append(cupertino_alert_dialog)
                cupertino_alert_dialog.open = True
                self.page.update()
                self.load_button.icon_color = ft.Colors.WHITE60
                self.load_button.update()
                return
            else:
                if self.pipeline_gui.pipeline.running:
                    self.pipeline_gui.page.open(
                        ft.SnackBar(ft.Text(f"Failed to load pipeline: a previous pipeline execution is still active!", color=ft.Colors.WHITE),
                                    bgcolor=ft.Colors.RED))
                    self.pipeline_gui.page.update()
                    return
                self.pipeline_storage.load_pipeline(e.files[0].path)

        self.load_button.icon_color = ft.Colors.WHITE60
        self.load_button.update()


    def on_file_saved(self, e):
        """
        Handles if a file gets saved.
        """
        if e.path is not None:
            if Path(e.path).suffix == "":
                e.path = e.path + ".csp"
            if Path(e.path).suffix != ".csp":
                self.pipeline_gui.page.open(ft.SnackBar(ft.Text(f"Pipeline name must have .csp suffix!",color=ft.Colors.WHITE),bgcolor=ft.Colors.RED))
                self.pipeline_gui.page.update()
                self.page.title = f"CellSePi - {self.pipeline_gui.pipeline_name}*"
                self.save_as_button.icon_color = ft.Colors.WHITE60
                self.page.update()
                return
            self.pipeline_storage.save_as_pipeline(e.path)
            self.pipeline_gui.page.open(ft.SnackBar(ft.Text(f"Pipeline saved at {e.path}",color=ft.Colors.WHITE),bgcolor=ft.Colors.GREEN))
            self.pipeline_gui.page.update()
            self.page.title = f"CellSePi - {self.pipeline_gui.pipeline_name}"
            self.save_button.icon_color = ft.Colors.WHITE24
            self.save_button.disabled = True
            self.page.update()

        self.save_as_button.icon_color = ft.Colors.WHITE60
        self.save_as_button.update()


    def press_page_forward(self):
        self.pipeline_gui.change_page(self.pipeline_gui.show_room_page_number+1)
        if self.pipeline_gui.show_room_page_number > 0:
            self.page_backward.icon_color = ft.Colors.WHITE60
            self.page_backward.disabled = False
            self.page_backward.update()
        if self.pipeline_gui.show_room_page_number >= self.pipeline_gui.show_room_max_page_number-1:
            self.page_forward.icon_color = ft.Colors.WHITE24
            self.page_forward.disabled = True
            self.page_forward.update()

    def press_page_backward(self):
        self.pipeline_gui.change_page(self.pipeline_gui.show_room_page_number-1)
        if self.pipeline_gui.show_room_page_number == 0:
            self.page_backward.icon_color = ft.Colors.WHITE24
            self.page_backward.disabled = True
            self.page_backward.update()
        if self.pipeline_gui.show_room_page_number < self.pipeline_gui.show_room_max_page_number-1:
            self.page_forward.icon_color = ft.Colors.WHITE60
            self.page_forward.disabled = False
            self.page_forward.update()

    def scroll_horizontal(self,e):
        self.scroll_horizontal_row.scroll_to((self.work_area.width-self.page.window.width)*e.control.value, duration=1000)
        self.scroll_horizontal_row.update()

    def run_menu_click(self):
        if self.run_menu.opacity==1:
            self.run_menu_button.icon_color = WHITE60
            self.run_menu_button.tooltip = f"Show run menu\n[Ctrl + R]"
            self.run_menu_button.update()
            self.run_menu.width = 0
            self.run_menu.opacity = 0
            self.run_menu.update()
        else:
            self.run_menu_button.icon_color = ft.Colors.BLUE_400
            self.run_menu_button.tooltip = f"Hide run menu\n[Ctrl + R]"
            self.run_menu_button.update()
            self.run_menu.width = 420
            self.run_menu.opacity = 1
            self.run_menu.update()

    def zoom_menu_click(self):
        if self.zoom_menu.opacity==1:
            self.zoom_menu_button.icon_color = WHITE60
            self.zoom_menu_button.tooltip = f"Show zoom menu\n[Ctrl + R]"
            self.zoom_menu_button.update()
            self.zoom_menu.width = 0
            self.zoom_menu.opacity = 0
            self.zoom_menu.update()
        else:
            self.zoom_menu_button.icon_color = ft.Colors.BLUE_400
            self.zoom_menu_button.tooltip = f"Hide zoom menu\n[Ctrl + R]"
            self.zoom_menu_button.update()
            self.zoom_menu.width = None
            self.zoom_menu.opacity = 1
            self.zoom_menu.update()

    def delete_button_click(self):
        if self.pipeline_gui.show_delete_button:
            self.delete_button.icon_color = WHITE60
            self.delete_button.tooltip = f"Show delete buttons\n[Ctrl + D]"
            self.pipeline_gui.show_delete_button = False
            self.pipeline_gui.lines_gui.update_all()
        else:
            self.delete_button.icon_color = ft.Colors.BLUE_400
            self.delete_button.tooltip = f"Hide delete buttons\n[Ctrl + D]"
            self.pipeline_gui.show_delete_button = True
            if self.pipeline_gui.show_ports:
                self.port_button_click()
            self.pipeline_gui.lines_gui.update_all()

        self.delete_button.update()

    def port_button_click(self):
        if self.pipeline_gui.show_ports:
            self.port_button.icon_color = WHITE60
            self.port_button.tooltip = f"Show which ports get transferred\n[Ctrl + P]"
            self.pipeline_gui.show_ports = False
            self.pipeline_gui.lines_gui.update_all()
        else:
            self.port_button.icon_color = ft.Colors.BLUE_400
            self.port_button.tooltip = f"Hide which ports get transferred\n[Ctrl + P]"
            self.pipeline_gui.show_ports = True
            if self.pipeline_gui.show_delete_button:
                self.delete_button_click()
            self.pipeline_gui.lines_gui.update_all()

        self.port_button.update()


    def setup(self):
        self.work_area = ft.Container(
            content=self.pipeline_gui,
            width=10000,
            height=10000,
            bgcolor=ft.Colors.TRANSPARENT,
        )

        self.interactive_view = FletExtendedInteractiveViewer(content=self.work_area, constrained=False,
                                                              height=self.page.window.height,
                                                              width=self.page.window.width, scale_enabled=True)

        def on_resize(e: ft.WindowResizeEvent):
            self.interactive_view.height = e.height-20
            self.interactive_view.width = e.width
            self.interactive_view.update()
            self.pipeline_gui.update_show_room()
            self.help_text.height = e.height
            self.help_text.width = e.width
            self.help_text.update()

        self.page.on_resized = on_resize

        self.builder_page_stack = ft.Stack([
                self.help_text,
                self.interactive_view,
                self.left_tools,
                self.right_tools,
                self.run_menu,
                self.zoom_menu,
             ]
            )
