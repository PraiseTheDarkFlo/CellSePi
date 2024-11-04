
import flet as ft
import flet.canvas as fc
import os


import gui_options as op

def gui(page: ft.Page,image_gallery: ft.ListView,directory_path: ft.Text):
    main_image = ft.Container(ft.Image(src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA\AAAFCAIAAAFe0wxPAAAAAElFTkSuQmCC",
                                       height=700, width=500, fit=ft.ImageFit.COVER,
                                                    expand=True,
                                                    aspect_ratio=2))
    def on_image_click(event,img_path):
        main_image.content = ft.Image(src=img_path, height=700, width=500, fit=ft.ImageFit.COVER,
                                                    expand=True,
                                                    aspect_ratio=2)
        page.update()

    # Ergebnisbehandler für die Dateiauswahl
    def pick_files_result(e: ft.FilePickerResultEvent):
        #TODO
        directory_path.value = "in development"
        formatted_path.value = format_directory_path(directory_path)
        formatted_path.update()

    count_results_txt = ft.Text(value="Results: 0")
    def update_results_text():
        count_results_txt.value = f"Results: {len(image_gallery.controls)}"
        count_results_txt.update()  # Text auf der UI aktualisieren

    pick_files_dialog = ft.FilePicker(on_result=pick_files_result)

    # Ergebnisbehandler für das Verzeichnis
    def get_directory_result(e: ft.FilePickerResultEvent):
        if e.path:
            directory_path.value = e.path
            load_images_from_directory(e.path)
        else:
            image_gallery.controls.clear()
            image_gallery.update()
        formatted_path.value = format_directory_path(directory_path)
        formatted_path.update()

    get_directory_dialog = ft.FilePicker(on_result=get_directory_result)

    # Bilder aus dem Verzeichnis laden
    def load_images_from_directory(path):
        image_files = [f for f in os.listdir(path) if
                       f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.lif', '.tif'))]
        images = [os.path.join(path, f) for f in image_files]
        load_images(images)

    # Bilder in die Galerie laden
    def load_images(images):
        image_gallery.controls.clear()
        for img_path in images:
            file_name = os.path.basename(img_path)
            file_name = file_name.split('.')[0]
            current_image = ft.Image(src=img_path, height=200, width=200, fit=ft.ImageFit.COVER)
            current_image_container = ft.GestureDetector(
                content=current_image,
                on_tap=lambda e, path=img_path: on_image_click(e, path)
            )
            img_container = ft.Column(
                [
                    ft.Text(file_name, weight="bold"),  # Name über dem Bild
                    current_image_container,
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=5  # Abstand zwischen Text und Bild
            )
            image_gallery.controls.append(img_container)
        image_gallery.update()
        update_results_text()


    # Switch zum Wechseln zwischen Dateien und Verzeichnis
    is_lif = ft.Switch(label="Lif", value=True)
    switch_mask = ft.Switch(label="Mask", value=True)

    tf_cp = ft.TextField(
        label="Channel Prefix:",
        border_color=ft.colors.BLUE_ACCENT
    )
    tf_d = ft.TextField(
        label="Diameter:",
        border_color=ft.colors.BLUE_ACCENT
    )
    tf_ms = ft.TextField(
        label="Masked Suffix:",
        border_color=ft.colors.BLUE_ACCENT
    )
    dropdown_bf_channel = ft.Dropdown(
        label="Bright Field Channel:",
        options=[#hier sollte je nach den bilder auswählbar sein welches bild das BrightFiled Channel ist...
            ft.dropdown.Option("1"),
            ft.dropdown.Option("2"),
            ft.dropdown.Option("3"),
            ft.dropdown.Option("4"),
        ],
        border_color=ft.colors.BLUE_ACCENT
    )


    # Buttons und Textanzeigen für Dateien und Verzeichnisse
    files_row = ft.Row(
        [
            ft.ElevatedButton(
                "Pick Files",
                icon=ft.icons.UPLOAD_FILE,
                on_click=lambda _: pick_files_dialog.pick_files(allow_multiple=True),
            )
        ],alignment=ft.MainAxisAlignment.END
    )


    pick_model_row = ft.Row(
        [#wenn es läuft könnte man anstatt Start segmentation cancel machen und progressbar nur wenn es gestartet ist sonst nur start button
            ft.ProgressBar(value=0.2,width=180),
            ft.Text("2%"),
            ft.ElevatedButton(
                "Start Segmentation",
                icon=ft.icons.PLAY_CIRCLE,
                disabled=True,
                on_click=lambda _: pick_files_dialog.pick_files(allow_multiple=False),
            )
        ],alignment=ft.MainAxisAlignment.END
    )
    directory_row = ft.Row(
        [
            ft.ElevatedButton(
                "Open Directory",
                icon=ft.icons.FOLDER_OPEN,
                on_click=lambda _: get_directory_dialog.get_directory_path(),
                disabled=page.web,
            ),
        ],alignment=ft.MainAxisAlignment.END
    )

    # Button-Aktion für den Switch
    def update_view(e):
        if is_lif.value:  # Wenn der Switch aktiviert ist
            files_row.visible = True
            directory_row.visible = False
        else:  # Wenn der Switch deaktiviert ist
            files_row.visible = False
            directory_row.visible = True
        page.update()
    def update_view_mask(e):
        if switch_mask.value:
            print("on")
        else:
            print("off")
        page.update()

    def format_directory_path(dir_path, max_length=30):
        # Teile den Pfad in seine Komponenten auf
        parts = dir_path.value.split('/')
        path = dir_path.value
        # Behalte die letzten beiden Teile und füge "..." hinzu, wenn der Pfad länger ist
        if len(dir_path.value) > max_length:
            if len(parts) > 2:
                path = f".../{parts[len(parts)-2]}/{parts[len(parts)-1]}"
            else:
                return f"...{path[len(parts)-(max_length - 3):]}"

        # Kürze den Pfad, wenn er die maximale Länge überschreitet
        if len(path) > max_length:
            # Kürze und füge "..." hinzu
            path = f"...{path[len(parts)-(max_length - 3):]}"  # 3 für '...'

        return path

    formatted_path = ft.Text(format_directory_path(directory_path),weight="bold")

    def copy_directory_to_clipboard(e):
        # Der Inhalt von `directory_path.value` wird in die Zwischenablage kopiert
        page.set_clipboard(directory_path.value)
        # Optional: Zeigt eine Benachrichtigung an, dass der Pfad kopiert wurde
        page.snack_bar = ft.SnackBar(ft.Text("Directory path copied to clipboard!"))
        page.snack_bar.open = True
        page.update()

    # Erstellen der anklickbaren Karte
    model_card = ft.Card(
        content=ft.Container(
            content=ft.Stack(
                [
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.ListTile(
                                    leading=ft.Icon(name=ft.icons.COMPUTER_ROUNDED),
                                    title=ft.Text("Model Name"),
                                ),
                                pick_model_row,
                            ]
                        )
                    ),
                    ft.Container(
                        content=ft.IconButton(
                            icon=ft.icons.UPLOAD_FILE,
                            tooltip="Chose Model",
                            on_click=lambda _: pick_files_dialog.pick_files(allow_multiple=False),
                        ),alignment=ft.alignment.bottom_right,
                    )
                ]
            ),
            width=page.width * (1 / 3),
            padding=10
        ),
    )
    directory_card = ft.Card(
        content=ft.Container(
                content=ft.Stack(
                    [
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.ListTile(
                                        leading=ft.Icon(name=ft.icons.FOLDER_OPEN),
                                        title=formatted_path,
                                        subtitle=count_results_txt
                                    ),ft.Row([is_lif,
                                    directory_row,
                                    files_row,],alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                                             )
                                ]
                            )
                        ),
                        ft.Container(
                            content=ft.Container(
                            content=ft.IconButton(
                                icon=ft.icons.COPY,
                                tooltip="Copy to clipboard",
                                on_click=copy_directory_to_clipboard
                            ),
                            alignment=ft.alignment.top_right,
                            ),
                            expand = True,
                        )
                    ]

            ),
            width=page.width*(1/3),
            padding=10,
            expand=True
        )
    )

    class State:
        x: float
        y: float

    state = State()

    def pan_start(e: ft.DragStartEvent):
        state.x = e.local_x
        state.y = e.local_y

    def pan_update(e: ft.DragUpdateEvent):
        canvas.shapes.append(
            fc.Line(
                state.x, state.y, e.local_x, e.local_y, paint=ft.Paint(stroke_width=3)
            )
        )
        canvas.update()
        state.x = e.local_x
        state.y = e.local_y
    canvas = fc.Canvas(

        content=ft.GestureDetector(
            on_pan_start=pan_start,
            on_pan_update=pan_update,
            drag_interval=10,
        ),
    )
    canvas_container = ft.Container(
        canvas,
        border_radius=5
    )


    # UI zusammenstellen
    page.overlay.extend([pick_files_dialog, get_directory_dialog])
    page.add(
        ft.Column(  # Hauptspalte für die gesamte UI
            [
                ft.Row(  # Linke und rechte Seite in einer Zeile anordnen
                    [
                        ft.Column(  # Linke Spalte mit Steuerungselementen
                            [

                                            ft.Card(
                                                    content=ft.Stack([main_image,canvas_container]),
                                                    width=700,
                                                    height=500,
                                                    expand=True,
                                                    aspect_ratio=2
                                            )


                                ,
                                ft.Row([switch_mask]),
                                ft.Row([dropdown_bf_channel,tf_cp]),
                                ft.Row([tf_ms,tf_d]),
                                model_card
                            ],
                            expand=True,
                            alignment=ft.MainAxisAlignment.START,
                        ),
                        ft.Column(  # Rechte Spalte mit Galerie und Verzeichnispfad
                            [
                                directory_card,
                                ft.Card(  # Galerie als Container
                                    content=image_gallery,
                                    width=page.width*(1/3),
                                    expand= True,
                                    aspect_ratio = 4
                                ),
                            ],
                            expand=True,
                        ),op.switch(page)
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,  # Abstand zwischen linkem und rechtem Bereich
                    expand=True,
                ),
            ],
            expand=True
        )
    )

    # Initiale Sichtbarkeit setzen
    update_view(None)  # Initiale Ansicht festlegen
    is_lif.on_change = update_view  # Ereignis für den Switch hinzufügen
    switch_mask.on_change = update_view_mask
