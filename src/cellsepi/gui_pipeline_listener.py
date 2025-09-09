from typing import Type
import flet as ft
from cellsepi.backend.main_window.expert_mode.listener import EventListener, OnPipelineChangeEvent, Event, \
    ModuleExecutedEvent, ProgressEvent, ErrorEvent, ModuleStartedEvent, DragAndDropEvent


class PipelineChangeListener(EventListener):
    def __init__(self,builder):
        self.event_type = OnPipelineChangeEvent
        self.builder = builder
    def get_event_type(self) -> Type[Event]:
        return self.event_type

    def update(self, event: Event) -> None:
        if not isinstance(event, self.get_event_type()):
            raise TypeError("The given event is not the right event type!")
        self._update(event)

    def _update(self, event: Event) -> None:
        if len(self.builder.pipeline_gui.modules) > 0:
            self.builder.help_text.opacity = 0
            self.builder.help_text.update()
            self.builder.save_button.icon_color = ft.Colors.WHITE60
            self.builder.save_button.disabled = False
            self.builder.save_button.update()
            if not self.builder.pipeline_gui.pipeline.running:
                self.builder.start_button.disabled = False
                self.builder.start_button.update()
        else:
            self.builder.help_text.opacity = 1
            self.builder.help_text.update()
            self.builder.save_button.icon_color = ft.Colors.WHITE24
            self.builder.save_button.disabled = True
            self.builder.save_button.update()
            self.builder.start_button.disabled = True
            self.builder.start_button.update()
        self.builder.update_modules_executed()

class DragAndDropListener(EventListener):
    def __init__(self,builder):
        self.event_type = DragAndDropEvent
        self.builder = builder
    def get_event_type(self) -> Type[Event]:
        return self.event_type

    def update(self, event: Event) -> None:
        if not isinstance(event, self.get_event_type()):
            raise TypeError("The given event is not the right event type!")
        self._update(event)

    def _update(self, event: Event) -> None:
        if len(self.builder.pipeline_gui.modules) == 0:
            if event.drag:
                self.builder.help_text.opacity = 0.60
                self.builder.help_text.update()
            else:
                self.builder.help_text.opacity = 1
                self.builder.help_text.update()

class ModuleExecutedListener(EventListener):
    def __init__(self,builder):
        self.event_type = ModuleExecutedEvent
        self.builder = builder
    def get_event_type(self) -> Type[Event]:
        return self.event_type

    def update(self, event: Event) -> None:
        if not isinstance(event, self.get_event_type()):
            raise TypeError("The given event is not the right event type!")
        self._update(event)

    def _update(self, event: Event) -> None:
        self.builder.pipeline_gui.modules[event.module_id].enable_tools()
        self.builder.pipeline_gui.modules_executed += 1
        if self.builder.pipeline_gui.source_module != "":
            self.builder.pipeline_gui.check_for_valid(event.module_id)
        self.builder.pipeline_gui.lines_gui.update_delete_buttons(self.builder.pipeline_gui.modules[event.module_id])
        self.builder.pipeline_gui.modules[event.module_id].pause_button.visible = False
        self.builder.pipeline_gui.modules[event.module_id].waiting_button.visible = False
        self.builder.pipeline_gui.modules[event.module_id].start_button.visible = True
        self.builder.pipeline_gui.modules[event.module_id].delete_button.visible = True
        self.builder.pipeline_gui.modules[event.module_id].pause_button.update()
        self.builder.pipeline_gui.modules[event.module_id].waiting_button.update()
        self.builder.pipeline_gui.modules[event.module_id].start_button.update()
        self.builder.pipeline_gui.modules[event.module_id].delete_button.update()
        self.builder.update_modules_executed()


class ModuleStartedListener(EventListener):
    def __init__(self,builder):
        self.event_type = ModuleStartedEvent
        self.builder = builder

    def get_event_type(self) -> Type[Event]:
        return self.event_type

    def update(self, event: Event) -> None:
        if not isinstance(event, self.get_event_type()):
            raise TypeError("The given event is not the right event type!")
        self._update(event)

    def _update(self, event: Event) -> None:
        self.builder.pipeline_gui.modules[event.module_id].set_running()
        self.builder.category_icon.color = self.builder.pipeline_gui.modules[event.module_id].module.gui_config().category.value
        self.builder.category_icon.update()
        self.builder.running_module.value = self.builder.pipeline_gui.modules[event.module_id].module.gui_config().name
        self.builder.running_module.update()

class ModuleProgressListener(EventListener):
    def __init__(self, builder):
        self.event_type = ProgressEvent
        self.builder = builder

    def get_event_type(self) -> Type[Event]:
        return self.event_type

    def update(self, event: Event) -> None:
        if not isinstance(event, self.get_event_type()):
            raise TypeError("The given event is not the right event type!")
        self._update(event)

    def _update(self, event: Event) -> None:
        self.builder.progress_bar_module.value = event.percent / 100
        self.builder.progress_bar_module.update()
        self.builder.progress_bar_module_text.value = f"{event.percent}%"
        self.builder.progress_bar_module_text.update()
        self.builder.info_text.value = event.process
        self.builder.info_text.spans = []
        self.builder.info_text.update()
        self.builder.page.update()

class ModuleErrorListener(EventListener):
    def __init__(self, builder):
        self.event_type = ErrorEvent
        self.builder = builder

    def get_event_type(self) -> Type[Event]:
        return self.event_type

    def update(self, event: Event) -> None:
        if not isinstance(event, self.get_event_type()):
            raise TypeError("The given event is not the right event type!")
        self._update(event)

    def _update(self, event: Event) -> None:
        self.builder.pipeline_gui.toggle_all_stuck_in_running()
        self.builder.info_text.value = ""
        self.builder.info_text.spans = [
        ft.TextSpan("Error: ", style=ft.TextStyle(weight=ft.FontWeight.BOLD, color=ft.Colors.RED)),
        ft.TextSpan(event.error_msg, style=ft.TextStyle(color=ft.Colors.WHITE60)),]
        self.builder.info_text.update()
        self.builder.page.update()
        self.builder.category_icon.color = ft.Colors.RED
        self.builder.category_icon.update()

