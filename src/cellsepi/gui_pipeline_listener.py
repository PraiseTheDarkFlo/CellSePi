from typing import Type

from cellsepi.backend.main_window.expert_mode.listener import EventListener, OnPipelineChangeEvent, Event, \
    ModuleExecutedEvent, ProgressEvent, ErrorEvent, ModuleStartedEvent


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
        self.builder.update_modules_executed()

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
        self.builder.pipeline_gui.modules_executed += 1
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
        print(event)

