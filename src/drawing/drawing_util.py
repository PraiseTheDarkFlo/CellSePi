import cv2
import numpy as np
from PyQt5.QtCore import QPointF


def mask_shifting(mask_data,deleted_mask_id:int):
    """
    Shifts the mask when a mask got deleted to restore an order without gaps.

    Args:
        mask_data (np.array): the mask data.
        deleted_mask_id (int): the id of the deleted mask.

    Raises:
          ValueError: if the deleted_mask_id is smaller or equal to 0.
    """
    if deleted_mask_id < 1:
        raise ValueError("deleted_mask_id must be greater than 0")

    mask = mask_data["masks"]
    outline = mask_data["outlines"]

    mask[mask>deleted_mask_id] -= 1
    outline[outline>deleted_mask_id] -= 1

def search_free_id(mask,outline):
    """
    Sucht in einem NumPy-Array von Ganzzahlen (z.B. [1,1,2,2,3,4,5,5,7,7])
    nach der ersten fehlenden Zahl (also hier 6).
    Falls keine Lücke vorhanden ist, wird der größte Wert + 1 zurückgegeben.
    """
    print("XXXX")
    combined = np.concatenate((mask.ravel(),outline.ravel()))
    print("NAME")
    unique_vals = np.unique(combined)

    # Falls das Array leer ist, kann man z.B. 1 zurückgeben
    if unique_vals.size == 0:
        return 1

    # Differenzen zwischen aufeinanderfolgenden Werten berechnen
    diffs = np.diff(unique_vals)

    # Suchen, ob es eine Lücke gibt (Differenz > 1)
    luecke_index = np.where(diffs > 1)[0]

    if luecke_index.size > 0:
        fehlender_wert = unique_vals[luecke_index[0]] + 1
    else:
        fehlender_wert = unique_vals[-1] + 1

    return fehlender_wert

def bresenham_line(start: QPointF, end: QPointF):
    """
    Berechnet alle Pixelkoordinaten entlang einer Linie von start bis end
    mithilfe des Bresenham-Algorithmus.
    """
    # Start- und Endkoordinaten auf ganze Zahlen runden
    x0, y0 = int(round(start.x())), int(round(start.y()))
    x1, y1 = int(round(end.x())), int(round(end.y()))
    pixels = []

    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy

    while True:
        pixels.append((x0, y0))
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x0 += sx
        if e2 < dx:
            err += dx
            y0 += sy

    return pixels


def trace_contour(binary_mask):
    y_indices, x_indices = np.where(binary_mask)
    start_idx = np.lexsort((x_indices, y_indices))[0]
    start_x, start_y = x_indices[start_idx], y_indices[start_idx]

    directions = [(0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1)]
    contour = []
    current = (start_x, start_y)
    prev = (start_x - 1, start_y)

    while True:
        contour.append(current)
        dir_idx = directions.index((prev[0] - current[0], prev[1] - current[1]))
        for i in range(8):
            next_dir = (dir_idx + 1 + i) % 8
            dx, dy = directions[next_dir]
            nx, ny = current[0] + dx, current[1] + dy
            if 0 <= ny < binary_mask.shape[0] and 0 <= nx < binary_mask.shape[1]:
                if binary_mask[ny, nx]:
                    prev = current
                    current = (nx, ny)
                    break
        if current == (start_x, start_y):
            break
    return contour

def fill_polygon_from_outline(contour, mask_shape):
    """
    Fills the given poly in contour with scanLine technique.
    """
    mask = np.zeros(mask_shape, dtype=np.uint8)
    if not contour:
        return mask

    edges = []
    num_vertices = len(contour)
    for i in range(num_vertices):
        x0, y0 = contour[i]
        x1, y1 = contour[(i + 1) % num_vertices]
        if y0 == y1:
            continue  # Skip horizontal edges
        if y0 > y1:
            x0, y0, x1, y1 = x1, y1, x0, y0  # Ensure y0 < y1
        slope = (x1 - x0) / (y1 - y0) if (y1 - y0) != 0 else 0
        edges.append((y0, y1, x0, slope))

    if not edges:
        return mask

    global_edge_table = sorted(edges, key=lambda e: (e[0], e[2]))
    scan_line = min(e[0] for e in global_edge_table)
    active_edges = []

    while global_edge_table or active_edges:
        # Add edges starting at the current scan line
        while global_edge_table and global_edge_table[0][0] == scan_line:
            e = global_edge_table.pop(0)
            active_edges.append([e[1], e[2], e[3]])

        active_edges.sort(key=lambda e: e[1])

        # Fill between pairs of edges
        for i in range(0, len(active_edges), 2):
            if i + 1 >= len(active_edges):
                break
            e1 = active_edges[i]
            e2 = active_edges[i + 1]
            x_start = int(np.ceil(e1[1]))
            x_end = int(np.floor(e2[1]))
            for x in range(x_start, x_end + 1):
                if 0 <= x < mask_shape[1] and 0 <= scan_line < mask_shape[0]:
                    mask[scan_line, x] = 1

        scan_line += 1
        active_edges = [e for e in active_edges if e[0] > scan_line]
        for e in active_edges:
            e[1] += e[2]

    return mask

def find_border_pixels(mask, outline, cell_id, threshold=1):
    """
    Findet Randpixel in einer gegebenen Maskenmatrix unter Berücksichtigung der Outline
    und sucht nur nach Pixeln, die mit der angegebenen cell_id übereinstimmen.

    Randpixel sind solche, deren benachbarte Pixel eine andere ID haben oder die im Outline
    als Rand markiert sind.

    :param mask: Eine 2D-Maske, die die ID jedes Pixels in der Fläche repräsentiert.
    :param outline: Eine 2D-Maske, die die Randpixel markiert (normalerweise mit 100).
    :param cell_id: Die ID der Zelle, nach deren Randpixeln gesucht werden soll.
    :param threshold: Ein Schwellenwert, um sicherzustellen, dass nur gültige Randpixel erfasst werden.
    :return: Eine Liste von Randpixel-Koordinaten (x, y).
    """
    border_pixels = []

    rows, cols = mask.shape
    for y in range(rows):
        for x in range(cols):
            # ID des aktuellen Pixels prüfen
            current_id = mask[y, x]

            # Wenn die ID des aktuellen Pixels nicht der gesuchten cell_id entspricht, überspringe es
            if current_id != cell_id:
                continue

            # Nachbarpositionen: oben, unten, links, rechts
            neighbors = [
                (y - 1, x), (y + 1, x),  # oben, unten
                (y, x - 1), (y, x + 1)  # links, rechts
            ]

            is_border_pixel = False

            # Überprüfe die Nachbarn auf unterschiedliche IDs oder Rand im Outline
            for ny, nx in neighbors:
                if 0 <= ny < rows and 0 <= nx < cols:  # Sicherstellen, dass der Nachbar im gültigen Bereich liegt
                    # Prüfen, ob der Nachbar eine andere ID hat oder im Outline als Rand markiert ist
                    if mask[ny, nx] != current_id and outline[ny, nx] != current_id:
                        is_border_pixel = True
                        break  # Sobald ein Nachbar gefunden wurde, der ungleich ist oder im Outline als Rand markiert ist, ist es ein Randpixel

            # Wenn es ein Randpixel ist, füge es der Liste hinzu
            if is_border_pixel:
                border_pixels.append((y,x))  # x, y Koordinaten (Spalte, Zeile)

    return border_pixels

