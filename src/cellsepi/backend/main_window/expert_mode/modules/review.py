import base64
import weakref
from io import BytesIO
from pathlib import Path

import numpy as np
import tifffile
from PIL import Image
from flet_extended_interactive_viewer import FletExtendedInteractiveViewer

from cellsepi.backend.main_window.data_util import convert_tiffs_to_png_parallel
from cellsepi.backend.main_window.expert_mode.listener import ProgressEvent
from cellsepi.backend.main_window.expert_mode.module import *
from cellsepi.backend.main_window.image_tuning import auto_adjust


class Review(Module, ABC):
    mask_color = (255, 0, 0)
    mask_opacity = 128
    outline_color = (0, 255, 0)
    _instances = []
    _gui_config = ModuleGuiConfig("Review",Categories.MANUAL,"This module allows you to manually review the given masks.")
    def __init__(self, module_id: str) -> None:
        self._module_id = module_id
        self._event_manager: EventManager = None
        self._inputs = {
            "image_paths": Port("image_paths", dict), #dict[str,dict[str,str]],
            "mask_paths": Port("mask_paths", dict), #dict[str,dict[str,str]]
        }
        self._outputs = {
            #"mask_paths": Port("mask_paths", dict), #dict[str,dict[str,str]] when i allow editing
        }

        padding = 20
        self._icon_x = {}
        self._icon_check = {}
        self.image_id = None
        self.channel_id = None
        self._selected_images_visualise = {}
        self._image_gallery = ft.ListView()
        self.user_segmentation_channel: str = "2"
        self._container_mask = ft.Container(
            ft.Image(src=r"data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA\AAAFCAIAAAFe0wxPAAAAAElFTkSuQmCC",
                     fit=ft.ImageFit.SCALE_DOWN, ), visible=False, alignment=ft.alignment.center,width=632,height=632)

        self._main_image = ft.Container(
            ft.Image(src=r"data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA\AAAFCAIAAAFe0wxPAAAAAElFTkSuQmCC",
                     fit=ft.ImageFit.SCALE_DOWN), alignment=ft.alignment.center,width=632,height=632)


        self._interactive_viewer = FletExtendedInteractiveViewer(content=ft.Stack([self._main_image, self._container_mask]),constrained=False,min_scale=0.1,width=632,height=632)
        zoom_value = 0.20
        self._mask_button = ft.IconButton(icon=ft.Icons.REMOVE_RED_EYE, icon_color=ft.Colors.WHITE24,
                              style=ft.ButtonStyle(
                                  shape=ft.RoundedRectangleBorder(radius=12), ),
                              on_click=lambda e: self.show_mask(),
                              tooltip="Show mask", hover_color=ft.Colors.WHITE12,disabled=True)
        self._slider_2d = ft.CupertinoSlidingSegmentedButton(
            selected_index=0,
            thumb_color=ft.Colors.BLUE_400,
            bgcolor=ft.Colors.WHITE12,
            on_change=lambda e:self.slider_update(e),
            padding=ft.padding.symmetric(0, 0),
            controls=[
                ft.Text("2D"),
                ft.Text("2.5D")
            ],
        )
        self._text_field_segmentation_channel = ft.TextField(
            border_color=ft.Colors.BLUE_ACCENT,
            value=self.user_segmentation_channel,
            on_blur=lambda e: self.on_change_sc(e),
            tooltip="Segmentation channel",
            height=30,width=70,content_padding=ft.padding.symmetric(0, 5),
        )
        self._slider_2_5d = ft.Slider(
            min=0, max=100, divisions=None, label="Slice: {value}", on_change=lambda e: self.slider_change(),visible=False,height=20,
            active_color=ft.Colors.BLUE_400,thumb_color=ft.Colors.BLUE_400
        )
        self._control_menu = ft.Container(ft.Container(ft.Row(
            [
                ft.IconButton(icon=ft.Icons.ZOOM_IN, icon_color=ft.Colors.WHITE60,
                              style=ft.ButtonStyle(
                                  shape=ft.RoundedRectangleBorder(radius=12), ),
                              on_click=lambda e:self._interactive_viewer.zoom(1.0 + zoom_value), tooltip="Zoom in",
                              hover_color=ft.Colors.WHITE12),
                ft.IconButton(icon=ft.Icons.ZOOM_OUT, icon_color=ft.Colors.WHITE60,
                              style=ft.ButtonStyle(
                                  shape=ft.RoundedRectangleBorder(radius=12), ), on_click=lambda e:self._interactive_viewer.zoom(1.0 - zoom_value), tooltip="Zoom out",
                              hover_color=ft.Colors.WHITE12),
                ft.IconButton(icon=ft.Icons.CROP_FREE, icon_color=ft.Colors.WHITE60,
                              style=ft.ButtonStyle(
                                  shape=ft.RoundedRectangleBorder(radius=12), ),on_click=lambda e:self._interactive_viewer.reset(400),
                              tooltip="Reset view", hover_color=ft.Colors.WHITE12),
                self._text_field_segmentation_channel,
                self._mask_button,
                self._slider_2d,
                self._slider_2_5d,
            ], spacing=2
        ), bgcolor=ft.Colors.BLACK54, expand=True, border_radius=ft.border_radius.vertical(top=0, bottom=12),
        )
        )
        self._main_image_view = ft.Card(
            content=ft.Column([ft.Container(self._interactive_viewer,padding=ft.padding.only(top=10),alignment=ft.alignment.top_center),self._control_menu]),
            width = 660, height = 700,
            expand=True,
        )

        self._settings: ft.Stack = ft.Stack([ft.Row([ft.Column([ft.Row([
                        self._main_image_view,ft.Card(content=ft.Container(self._image_gallery,width=600,height=700,expand=True,padding=20),expand=True),
                    ])
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,)],alignment=ft.MainAxisAlignment.CENTER),])
        Review._instances.append(self)

    @classmethod
    def gui_config(cls) -> ModuleGuiConfig:
       return cls._gui_config

    @property
    def module_id(self) -> str:
        return self._module_id

    @module_id.setter
    def module_id(self,value: str):
        self._module_id = value

    @property
    def inputs(self) -> dict[str, Port]:
        return self._inputs

    @property
    def outputs(self) -> dict[str, Port]:
        return self._outputs

    @property
    def settings(self) -> ft.Stack:
        return self._settings

    @property
    def event_manager(self) -> EventManager:
        return self._event_manager

    @event_manager.setter
    def event_manager(self, value: EventManager):
        self._event_manager = value

    def run(self):
        #reset
        self._icon_x = {}
        self._icon_check = {}
        self.image_id = None
        self.channel_id = None
        self._selected_images_visualise = {}
        self._image_gallery.clean()
        self._main_image.content.src=r"data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA\AAAFCAIAAAFe0wxPAAAAAElFTkSuQmCC"
        self._main_image.content.src_base64 = None
        self._main_image.update()
        self._container_mask.visible = False
        self._container_mask.update()

        self.event_manager.notify(ProgressEvent(percent=0, process=f"Loading Images: Starting"))
        src  = convert_tiffs_to_png_parallel(self.inputs["image_paths"].data)
        n_series = len(src)
        for iN,image_id in enumerate(src):
            cur_image_paths = src[image_id]

            self._selected_images_visualise[image_id] = {}
            for iN2,channel_id in enumerate(cur_image_paths):
                self._selected_images_visualise[image_id][channel_id] = ft.Container(
                    width=154,
                    height=154,
                    border=ft.border.all(4, ft.Colors.ORANGE_700),
                    alignment=ft.alignment.center,
                    visible=False,
                    padding=5
                )
                if iN == 0 and iN2 == 0:
                    image = tifffile.imread(self.inputs["image_paths"].data[image_id][channel_id])
                    if image.ndim == 3:
                        self._slider_2_5d.value = 0
                        self._slider_2_5d.max = image.shape[2] - 1
                        self._slider_2_5d.divisions = image.shape[2] - 2
                        self._slider_2_5d.disabled = False
                        self._slider_2_5d.update()
                    else:
                        self._slider_2_5d.value = 0
                        self._slider_2_5d.max = 1
                        self._slider_2_5d.divisions = None
                        self._slider_2_5d.disabled = True
                        self._slider_2_5d.update()

            group_row = ft.Row(
                [
                    ft.Column(
                    [
                            ft.GestureDetector(
                                content=ft.Container(ft.Stack([ft.Image(
                                src_base64=cur_image_paths[channel_id],
                                height=150,
                                width=150,
                                fit=ft.ImageFit.CONTAIN
                                ),self._selected_images_visualise[image_id][channel_id]]),width=156,height=156),
                                on_tap=lambda e, img_id=image_id, c_id=channel_id: self.update_main_image(img_id, c_id),
                            ),
                            ft.Text(channel_id, size=10, text_align=ft.TextAlign.CENTER),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=5
                    )
                    for channel_id in cur_image_paths
                ],
                alignment=ft.MainAxisAlignment.START,
                spacing=10,
                scroll=ft.ScrollMode.AUTO,
            )
            self._icon_check[image_id] = ft.Icon(ft.Icons.CHECK, color=ft.Colors.GREEN, size=17, visible=False,
                                                tooltip="Mask is available")
            self._icon_x[image_id] = ft.Icon(ft.Icons.CLOSE, size=17, visible=True, tooltip="Mask not available")
            self.update_mask_check(image_id)
            self._image_gallery.controls.append(ft.Column([ft.Row(
            [ft.Text(f"{image_id}", weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER), self._icon_check[image_id], self._icon_x[image_id]], spacing=2),
                                                      group_row], spacing=10, alignment=ft.MainAxisAlignment.CENTER))
            self.event_manager.notify(ProgressEvent(percent=int((iN+1) / n_series * 100), process=f"Loading Images: {iN+1}/{n_series}"))

        self.event_manager.notify(ProgressEvent(percent=100, process=f"Loading Images: Finished"))


    def update_mask_check(self, image_id):
        """
        Updates the symbol next to series number of image to a check or x, depending on if the corresponding image is available.
        Args:
            image_id: the id of the image to check mask availability
        """
        if self.inputs["mask_paths"].data is not None and image_id in self.inputs["mask_paths"].data and self.user_segmentation_channel in self.inputs["mask_paths"].data[image_id]:
            self._icon_check[image_id].visible = True
            self._icon_x[image_id].visible = False
        else:
            self._icon_check[image_id].visible = False
            self._icon_x[image_id].visible = True
        self._image_gallery.update()

    def update_all_masks_check(self):
        """
        Updates the symbol next to series number of image for every image_id in mask_paths.
        """
        if self.inputs["image_paths"].data is not None:
            for image_id in self.inputs["image_paths"].data:
                self.update_mask_check(image_id)

    def update_main_image(self,img_id,channel_id,on_click = True):
        """
        Method that handles what happens when the image is clicked or the main image need an update.
        """
        if on_click:
            if self.image_id is not None and self.image_id in self._selected_images_visualise:
                if self.channel_id is not None and self.channel_id in self._selected_images_visualise[self.image_id]:
                    self._selected_images_visualise[self.image_id][self.channel_id].visible = False
                    self._selected_images_visualise[self.image_id][self.channel_id].update()
        self.image_id = img_id
        self.channel_id = channel_id
        self._selected_images_visualise[img_id][channel_id].visible = True
        self._selected_images_visualise[img_id][channel_id].update()


        self._main_image.content.src_base64 = auto_adjust(self.inputs["image_paths"].data[img_id][channel_id], get_slice=int(self._slider_2_5d.value))
        self._main_image.update()
        if self.inputs["mask_paths"].data is not None and self.image_id in self.inputs["mask_paths"].data and self.user_segmentation_channel in self.inputs["mask_paths"].data[img_id]:
            if not self._container_mask.visible:
                self._mask_button.icon_color = ft.Colors.WHITE60
                self._mask_button.tooltip = "Show mask"
                self._mask_button.disabled = False
                self._mask_button.update()
            mask_data = np.load(Path(self.inputs["mask_paths"].data[self.image_id][self.user_segmentation_channel]), allow_pickle=True).item()

            mask= mask_data["masks"]
            outline = mask_data["outlines"]
            self._container_mask.content.src_base64 = self.convert_npy_to_canvas(mask,outline)
            self._container_mask.update()
        else:
            self._mask_button.tooltip = "Show mask"
            self._mask_button.icon_color = ft.Colors.WHITE24
            self._mask_button.disabled = True
            self._mask_button.update()
            self._container_mask.visible = False
            self._container_mask.update()

    def show_mask(self):
        self._mask_button.icon_color = ft.Colors.BLUE_400 if not self._container_mask.visible else ft.Colors.WHITE60
        self._mask_button.update()
        self._mask_button.tooltip="Show mask" if self._container_mask.visible else "Hide mask"
        self._container_mask.visible = not self._container_mask.visible
        self._container_mask.update()


    def convert_npy_to_canvas(self,mask, outline):
        """
        handles the conversion of the given file data

        Args:
            mask= the mask data stored in the numpy directory
            outline= the outline data stored in the numpy directory
        """
        buffer= BytesIO()

        if mask.ndim == 3:
            if self._slider_2_5d.visible:
                mask = np.transpose(mask, (1, 2, 0))
                mask = np.take(mask, int(self._slider_2_5d.value), axis=2)
            else:
                mask = np.transpose(mask, (1, 2, 0))
                mask = np.max(mask, axis=2)

        if outline.ndim == 3:
            if self._slider_2_5d.visible:
                outline = np.transpose(outline, (1, 2, 0))
                outline = np.take(outline, int(self._slider_2_5d.value), axis=2)
            else:
                outline = np.transpose(outline, (1, 2, 0))
                outline = np.max(outline, axis=2)

        image_mask = np.zeros(shape=(mask.shape[0], mask.shape[1], 4), dtype=np.uint8)
        r,g,b = self.mask_color
        image_mask[mask != 0] = (r, g, b, self.mask_opacity)
        r, g, b = self.outline_color
        image_mask[outline != 0] = (r, g, b, 255)
        im= Image.fromarray(image_mask).convert("RGBA")
        im.resize(size=(700,500))

        #saves the image as a image(base64)
        im.save(buffer, format="PNG")
        buffer.seek(0)
        image_base_64= base64.b64encode(buffer.getvalue()).decode('utf-8')

        #saves the created output image.
        return image_base_64


    def slider_update(self, e):
        if int(e.data) == 1:
            self._slider_2_5d.visible = True
        else:
            self._slider_2_5d.visible = False

        self.slider_change()
        self._slider_2_5d.update()

    def slider_change(self):
        if self.image_id is not None:
            self.update_main_image(self.image_id, self.channel_id)

    def on_change_sc(self,e):
        self.user_segmentation_channel = str(e.control.value)
        self.update_all_masks_check()
        if self.image_id is not None:
            self.update_main_image(self.image_id, self.channel_id)

    @classmethod
    def update_class(cls):
        for instance in cls._instances:
            if instance.image_id is not None:
                instance.update_main_image(instance.image_id, instance.channel_id)

    def destroy(self):
        self._instances.remove(self)
        super().destroy()