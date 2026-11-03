import math
import json
import os
import tkinter as tk
from tkinter import ttk, messagebox
from Commands import Validate
from PIL import Image, ImageTk, ImageDraw, ImageFont

# -----------------------------------------
# DISPLAY SETTINGS
# -----------------------------------------

GRID_VISIBLE = True
_ACTIVE_REDRAW = None

def setGridVisible(visible):

    global GRID_VISIBLE

    GRID_VISIBLE = bool(visible)

    # Immediately redraw the active preview.
    if _ACTIVE_REDRAW is not None:
        _ACTIVE_REDRAW()

# ---------------------------------------------------------
# PANE MANAGEMENT
# ---------------------------------------------------------

def clearPane(pane):
    """Destroy all widgets currently inside a pane."""

    for widget in pane.winfo_children():
        widget.destroy()


def clearPreview(shape_pane, preview_pane):
    """Clear both the Shape List and Preview panes."""

    clearPane(shape_pane)
    clearPane(preview_pane)

    # Remove references to previous preview data.
    for attribute in ("text_widget", "image", "canvas", "drawing_data"):
        if hasattr(preview_pane, attribute):
            delattr(preview_pane, attribute)

    if hasattr(shape_pane, "text_widget"):
        delattr(shape_pane, "text_widget")


# ---------------------------------------------------------
# RAW FILE REPRESENTATION
# ---------------------------------------------------------

def previewRawData(path, shape_pane):
    """
    Display the raw bytes of a file in the Shape List pane.

    Each row contains:
        - Byte offset
        - Hexadecimal representation
        - Binary representation
    """

    with open(path, "rb") as file:
        raw_data = file.read()

    text_widget = tk.Text(
        shape_pane,
        wrap="none",
        font=("Consolas", 10),
        state="normal"
    )

    text_widget.pack(fill="both", expand=True, padx=5, pady=5)

    text_widget.insert(
        "1.0",
        f"File: {os.path.basename(path)}\n"
        f"Size: {len(raw_data)} bytes\n\n"
    )

    text_widget.insert(
        "end",
        "OFFSET       HEX BYTES                                      BINARY BYTES\n"
    )

    text_widget.insert(
        "end",
        "-" * 110 + "\n"
    )

    for offset in range(0, len(raw_data), 8):

        chunk = raw_data[offset:offset + 8]

        hex_values = " ".join(f"{byte:02X}" for byte in chunk)

        binary_values = " ".join(f"{byte:08b}" for byte in chunk)

        text_widget.insert(
            "end",
            f"{offset:08X}     {hex_values:<35} {binary_values}\n"
        )

    text_widget.config(state="disabled")

    shape_pane.text_widget = text_widget

    return raw_data


# ---------------------------------------------------------
# TEXT FILE PREVIEW
# ---------------------------------------------------------

def previewText(path, preview_pane):
    """
    Interpret a file as UTF-8 text and display it
    in an editable Preview pane.
    """

    with open(path, "r", encoding="utf-8", errors="replace") as file:
        contents = file.read()

    previewTextContent(contents, preview_pane)


def previewTextContent(contents, preview_pane):
    """Display supplied text in an editable Text widget."""

    text_widget = tk.Text(
        preview_pane,
        wrap="none",
        font=("Consolas", 11),
        undo=True
    )

    text_widget.pack(fill="both", expand=True, padx=5, pady=5)

    text_widget.insert("1.0", contents)

    text_widget.config(state="normal")

    preview_pane.text_widget = text_widget


# ---------------------------------------------------------
# JSON FILE HANDLING
# ---------------------------------------------------------

def previewJSON(path, shape_pane, preview_pane):
    """
    Interpret a JSON file as a House Drafter structure.

    Approved structure:
        {
            "id": "unique-id",
            "dimension": 2,
            "units": "mm",
            "primitives": [
                {
                    "type": "line",
                    "start": [0, 0],
                    "end": [100, 100],
                    "color": "#FFFFFF"
                }
            ]
        }

    Valid structures:
        Shape List = formatted JSON
        Preview = rendered drawing

    Invalid structures:
        Shape List = raw file contents
        Preview = editable text

    Unsupported structures:
        Shape List = formatted JSON
        Preview = explanatory message

    Returns:
        bool: Whether the file was successfully interpreted.
    """

    # -----------------------------------------------------
    # 1. Clear existing pane contents
    # -----------------------------------------------------

    for widget in shape_pane.winfo_children():
        widget.destroy()

    for widget in preview_pane.winfo_children():
        widget.destroy()

    # -----------------------------------------------------
    # 2. Load JSON file
    # -----------------------------------------------------

    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)

    except json.JSONDecodeError:
        previewRawData(path, shape_pane)
        previewText(path, preview_pane)
        return False

    except UnicodeDecodeError:
        previewRawData(path, shape_pane)
        previewText(path, preview_pane)
        return False

    except OSError as error:
        ttk.Label(
            shape_pane,
            text=f"Unable to read JSON file:\n{error}",
            justify="left"
        ).pack(padx=10, pady=10, anchor="w")

        return False

    # -----------------------------------------------------
    # 3. Validate House Drafter structure
    # -----------------------------------------------------

    valid, errors = Validate.validate(data)

    if not valid:

        previewRawData(path, shape_pane)
        previewText(path, preview_pane)

        return False

    # -----------------------------------------------------
    # 4. Display valid JSON in Shape List
    # -----------------------------------------------------

    formatted = json.dumps(
        data,
        indent=4,
        ensure_ascii=False
    )

    previewTextContent(
        formatted,
        shape_pane
    )

    shape_pane.text_widget.config(
        state="disabled"
    )

    # -----------------------------------------------------
    # 5. Interpret dimensionality
    # -----------------------------------------------------

    if data["dimension"] == 2:

        try:
            previewDrawing(
                data,
                preview_pane
            )

            return True

        except Exception as error:

            ttk.Label(
                preview_pane,
                text=f"Unable to render drawing:\n{error}",
                justify="left"
            ).pack(padx=10, pady=10, anchor="w")

            return False

    # -----------------------------------------------------
    # 6. Future 3D support
    # -----------------------------------------------------

    if data["dimension"] == 3:

        ttk.Label(
            preview_pane,
            text=(
                "3D Structure Recognized\n\n"
                "This file contains a valid 3D object, "
                "but 3D preview support has not yet "
                "been implemented."
            ),
            justify="center"
        ).pack(
            fill="both",
            expand=True
        )

        return False

    # -----------------------------------------------------
    # 7. Unsupported dimensionality
    # -----------------------------------------------------

    ttk.Label(
        preview_pane,
        text="Unsupported dimensionality.",
        justify="center"
    ).pack(
        fill="both",
        expand=True
    )

    return False

# ---------------------------------------------------------
# IMAGE PREVIEW
# ---------------------------------------------------------

def previewImage(path, preview_pane):
    """Display an image in the Preview pane using Pillow."""

    try:
        image = Image.open(path)
        image.thumbnail(
            (max(preview_pane.winfo_width() - 30, 100),
             max(preview_pane.winfo_height() - 30, 100)),
            Image.Resampling.LANCZOS
        )

        photo = ImageTk.PhotoImage(image)

        image_label = ttk.Label(
            preview_pane,
            image=photo
        )

        image_label.pack(expand=True)

        # Keep a reference to prevent garbage collection.
        preview_pane.image = photo

    except Exception as error:
        messagebox.showerror(
            "Image Error",
            f"Unable to display image:\n{error}"
        )

# ---------------------------------------------------------
# 2D DRAWING RENDERER
# ---------------------------------------------------------



def previewDrawing(data, preview_pane):
    """
    Optimized 2D drawing renderer.

    Features:
        - Cached drawing bounds
        - Cached fonts
        - 1x interactive rendering
        - 3x final-quality rendering
        - Debounced redraws
        - Cursor-centred zoom
        - Middle/right mouse drag to pan
        - Reused Canvas image item
        - Automatic redraw when resized
    """

    canvas = tk.Canvas(
        preview_pane,
        background="white",
        highlightthickness=0,
        cursor="crosshair"
    )

    canvas.pack(fill="both", expand=True, padx=5, pady=5)

    preview_pane.canvas = canvas
    preview_pane.drawing_data = data

    # -------------------------------------------------
    # DRAWING UNITS
    # -------------------------------------------------

    units = data.get("units")

    if units != "mm":
        raise ValueError(
            "Unsupported drawing units. "
            "The renderer currently supports millimetres (mm) only."
        )

    primitives = data["primitives"]

    # -------------------------------------------------
    # VIEW SETTINGS
    # -------------------------------------------------

    view = {
        "zoom": 1.0,
        "pan_x": 0.0,
        "pan_y": 0.0,
        "drag_x": 0.0,
        "drag_y": 0.0,
        "cursor_x": None,
        "cursor_y": None
    }

    MIN_ZOOM = 0.1
    MAX_ZOOM = 20.0

    ZOOM_FACTOR = 1.1
    ZOOM_FACTOR_FAST = 1.25

    INTERACTIVE_QUALITY = 1
    FINAL_QUALITY = 3

    # -------------------------------------------------
    # RENDER STATE
    # -------------------------------------------------

    render_state = {
        "image_item": None,
        "photo": None,
        "preview_job": None,
        "final_job": None,
        "last_size": None
    }

    font_cache = {}

    # -------------------------------------------------
    # PRECOMPUTE DRAWING BOUNDS
    # -------------------------------------------------

    bounds_points = []

    for primitive in primitives:

        kind = primitive["type"]

        if kind == "point":
            bounds_points.append(primitive["position"])

        elif kind == "line":
            bounds_points.extend([
                primitive["start"],
                primitive["end"]
            ])

        elif kind in ("polyline", "polygon"):
            bounds_points.extend(primitive["points"])

        elif kind in ("circle", "arc"):

            cx, cy = primitive["center"]
            radius = primitive["radius"]

            bounds_points.extend([
                [cx - radius, cy - radius],
                [cx + radius, cy + radius]
            ])

        elif kind == "text":
            bounds_points.append(primitive["position"])

    if bounds_points:

        min_x = min(point[0] for point in bounds_points)
        max_x = max(point[0] for point in bounds_points)

        min_y = min(point[1] for point in bounds_points)
        max_y = max(point[1] for point in bounds_points)

    else:
        min_x = max_x = 0
        min_y = max_y = 0

    drawing_width = max(max_x - min_x, 1)
    drawing_height = max(max_y - min_y, 1)

    # -------------------------------------------------
    # STATUS READOUT
    # -------------------------------------------------

    MARGIN = 30

    def get_grid_spacing(scale):

        target_spacing = 36 / scale

        magnitude = 10 ** math.floor(
            math.log10(target_spacing)
        )

        normalized = target_spacing / magnitude

        if normalized <= 1:
            return magnitude

        elif normalized <= 2:
            return 2 * magnitude

        elif normalized <= 5:
            return 5 * magnitude

        else:
            return 10 * magnitude

    # Background and text are separate Canvas objects
    # so the readout remains legible over the drawing.

    readout_bg = canvas.create_rectangle(
        0, 0, 0, 0,
        fill="white",
        outline="#CCCCCC",
        width=1
    )

    readout_text = canvas.create_text(
        0, 0,
        anchor="sw",
        fill="#333333",
        font=("Consolas", 9)
    )

    def update_readout():

        width = canvas.winfo_width()
        height = canvas.winfo_height()

        if width <= 1 or height <= 1:
            return

        if not bounds_points:

            text = "Grid: N/A   X: N/A   Y: N/A"

        else:

            base_scale = min(
                (width - MARGIN * 2) / drawing_width,
                (height - MARGIN * 2) / drawing_height
            )

            scale = base_scale * view["zoom"]

            grid_spacing = get_grid_spacing(scale)

            if view["cursor_x"] is None:

                cursor_text = "X: --   Y: --"

            else:

                world_x = (
                    min_x
                    + (
                        view["cursor_x"]
                        - MARGIN
                        - view["pan_x"]
                    ) / scale
                )

                world_y = (
                    min_y
                    + (
                        height
                        - MARGIN
                        + view["pan_y"]
                        - view["cursor_y"]
                    ) / scale
                )

                cursor_text = (
                    f"X: {world_x:,.2f} {units}   "
                    f"Y: {world_y:,.2f} {units}"
                )

            text = (
                f"Grid: {grid_spacing:g} {units}   "
                f"{cursor_text}"
            )

        canvas.itemconfigure(
            readout_text,
            text=text
        )

        # Position the readout in the bottom-left corner.
        canvas.coords(
            readout_text,
            10,
            height - 10
        )

        # Fit the background around the text.
        bbox = canvas.bbox(readout_text)

        if bbox:

            padding = 5

            canvas.coords(
                readout_bg,
                bbox[0] - padding,
                bbox[1] - padding,
                bbox[2] + padding,
                bbox[3] + padding
            )

        # Keep the readout above the rendered drawing.
        canvas.tag_raise(readout_bg)
        canvas.tag_raise(readout_text)

    # -------------------------------------------------
    # FONT CACHE
    # -------------------------------------------------

    def getFont(size):

        size = max(1, int(size))

        if size in font_cache:
            return font_cache[size]

        try:
            font = ImageFont.truetype(
                "arial.ttf",
                size
            )

        except OSError:

            try:
                font = ImageFont.truetype(
                    "DejaVuSans.ttf",
                    size
                )

            except OSError:
                font = ImageFont.load_default()

        # Keep the cache bounded.
        if len(font_cache) >= 128:
            oldest_key = next(iter(font_cache))
            del font_cache[oldest_key]

        font_cache[size] = font

        return font

    # -------------------------------------------------
    # LINEWEIGHT
    # -------------------------------------------------

    def getLineWidth(primitive, quality, scale):
        """
        Calculate line thickness.

        Lineweight is expressed in millimetres and scales
        proportionally with the drawing's zoom level.
        """

        lineweight = primitive.get("lineweight", 0.35)

        pixels = lineweight * scale * quality

        return max(1, round(pixels))

    # -------------------------------------------------
    # RENDER
    # -------------------------------------------------

    def render(quality=FINAL_QUALITY):

        width = canvas.winfo_width()
        height = canvas.winfo_height()

        if width <= 1 or height <= 1:
            return

        S = quality

        image = Image.new(
            "RGB",
            (width * S, height * S),
            "white"
        )

        draw = ImageDraw.Draw(image)

        if not bounds_points:

            draw.text(
                (width * S / 2, height * S / 2),
                "No drawable geometry",
                fill="black",
                anchor="mm"
            )

        else:

            margin = 30

            base_scale = min(
                (width - margin * 2) / drawing_width,
                (height - margin * 2) / drawing_height
            )

            scale = base_scale * view["zoom"]

            # -----------------------------------------
            # COORDINATE TRANSFORMATION
            # -----------------------------------------

            def transform(point):

                x, y = point

                screen_x = (
                    margin
                    + (x - min_x) * scale
                    + view["pan_x"]
                )

                screen_y = (
                    height
                    - margin
                    - (y - min_y) * scale
                    + view["pan_y"]
                )

                return (
                    screen_x * S,
                    screen_y * S
                )


            # -----------------------------------------
            # BACKGROUND GRID
            # -----------------------------------------

            def draw_grid():

                grid_spacing = get_grid_spacing(scale)

                # Determine visible drawing coordinates.
                left = min_x + (-margin - view["pan_x"]) / scale
                right = min_x + (width - margin - view["pan_x"]) / scale

                bottom = min_y + (view["pan_y"] - margin) / scale
                top = min_y + (height - margin + view["pan_y"]) / scale

                # Grid index ranges.
                first_x = math.floor(left / grid_spacing)
                last_x = math.ceil(right / grid_spacing)

                first_y = math.floor(bottom / grid_spacing)
                last_y = math.ceil(top / grid_spacing)

                # Grid line appearance.
                minor_color = "#EEEEEE"
                major_color = "#DCDCDC"

                grid_width = 1 * S

                # Vertical grid lines.
                for index in range(first_x, last_x + 1):

                    x = index * grid_spacing

                    screen_x, _ = transform((x, 0))

                    # Align to the supersampling pixel grid.
                    screen_x = round(screen_x / S) * S

                    is_major = index % 5 == 0

                    draw.line(
                        (
                            screen_x,
                            0,
                            screen_x,
                            height * S
                        ),
                        fill=major_color if is_major else minor_color,
                        width=grid_width
                    )

                # Horizontal grid lines.
                for index in range(first_y, last_y + 1):

                    y = index * grid_spacing

                    _, screen_y = transform((0, y))

                    # Align to the supersampling pixel grid.
                    screen_y = round(screen_y / S) * S

                    is_major = index % 5 == 0

                    draw.line(
                        (
                            0,
                            screen_y,
                            width * S,
                            screen_y
                        ),
                        fill=major_color if is_major else minor_color,
                        width=grid_width
                    )

            # -----------------------------------------
            # VIEWPORT CULLING
            # -----------------------------------------

            def is_visible(primitive):

                kind = primitive["type"]

                padding = 10 * S

                # POINT
                if kind == "point":

                    x, y = transform(
                        primitive["position"]
                    )

                    radius = (
                        primitive.get("size", 2.0)
                        * scale * S / 2
                    )

                    padding = max(
                        padding,
                        radius
                    )

                    return (
                        -padding <= x <= width * S + padding
                        and
                        -padding <= y <= height * S + padding
                    )

                # LINE
                elif kind == "line":

                    coordinates = [
                        transform(primitive["start"]),
                        transform(primitive["end"])
                    ]

                # POLYLINE / POLYGON
                elif kind in ("polyline", "polygon"):

                    coordinates = [
                        transform(point)
                        for point in primitive["points"]
                    ]

                    if not coordinates:
                        return False

                # CIRCLE / ARC
                elif kind in ("circle", "arc"):

                    cx, cy = transform(
                        primitive["center"]
                    )

                    radius = (
                        primitive["radius"] * scale * S
                    )

                    coordinates = [
                        (cx - radius, cy - radius),
                        (cx + radius, cy + radius)
                    ]

                # TEXT
                elif kind == "text":

                    x, y = transform(
                        primitive["position"]
                    )

                    font_size = max(
                        1,
                        round(
                            primitive.get("height", 3.5)
                            * scale * S
                        )
                    )

                    font = getFont(font_size)

                    bbox = font.getbbox(
                        primitive["text"]
                    )

                    text_width = max(
                        1,
                        bbox[2] - bbox[0]
                    )

                    text_height = max(
                        1,
                        bbox[3] - bbox[1]
                    )

                    # Conservative allowance for text extent
                    # and rotation around its centre.
                    text_padding = (
                        max(text_width, text_height) * 2
                        + padding
                    )

                    return (
                        -text_padding <= x <= width * S + text_padding
                        and
                        -text_padding <= y <= height * S + text_padding
                    )

                else:
                    return False

                min_x_screen = min(
                    point[0] for point in coordinates
                )

                max_x_screen = max(
                    point[0] for point in coordinates
                )

                min_y_screen = min(
                    point[1] for point in coordinates
                )

                max_y_screen = max(
                    point[1] for point in coordinates
                )

                return not (
                    max_x_screen < -padding
                    or min_x_screen > width * S + padding
                    or max_y_screen < -padding
                    or min_y_screen > height * S + padding
                )

            # -------------------------------------
            # DRAW GRID (TEMPORARY DIAGNOSTIC)
            # -------------------------------------

            if GRID_VISIBLE:
                draw_grid()

            # -----------------------------------------
            # DRAW PRIMITIVES
            # -----------------------------------------

            for primitive in primitives:

                if not is_visible(primitive):
                    continue

                kind = primitive["type"]
                color = primitive["color"]

                line_width = getLineWidth(
                    primitive,
                    S,
                    scale
                )

                # POINT
                if kind == "point":

                    x, y = transform(
                        primitive["position"]
                    )

                    point_size = primitive.get(
                        "size",
                        2.0
                    )

                    radius = max(
                        0.5,
                        point_size * scale * S / 2
                    )

                    draw.ellipse(
                        (
                            x - radius,
                            y - radius,
                            x + radius,
                            y + radius
                        ),
                        fill=color,
                        outline=color
                    )

                # LINE
                elif kind == "line":

                    p1 = transform(
                        primitive["start"]
                    )

                    p2 = transform(
                        primitive["end"]
                    )

                    draw.line(
                        [p1, p2],
                        fill=color,
                        width=line_width
                    )

                # POLYLINE / POLYGON
                elif kind in ("polyline", "polygon"):

                    coordinates = [
                        transform(point)
                        for point in primitive["points"]
                    ]

                    if kind == "polygon":
                        coordinates.append(
                            coordinates[0]
                        )

                    if len(coordinates) >= 2:

                        draw.line(
                            coordinates,
                            fill=color,
                            width=line_width,
                            joint="curve"
                        )

                # CIRCLE
                elif kind == "circle":

                    cx, cy = transform(
                        primitive["center"]
                    )

                    radius = (
                        primitive["radius"] * scale * S
                    )

                    draw.ellipse(
                        (
                            cx - radius,
                            cy - radius,
                            cx + radius,
                            cy + radius
                        ),
                        outline=color,
                        width=line_width
                    )

                # ARC
                elif kind == "arc":

                    cx, cy = transform(
                        primitive["center"]
                    )

                    radius = (
                        primitive["radius"] * scale * S
                    )

                    start = primitive["start_angle"]
                    end = primitive["end_angle"]

                    draw.arc(
                        (
                            cx - radius,
                            cy - radius,
                            cx + radius,
                            cy + radius
                        ),
                        start=-end,
                        end=-start,
                        fill=color,
                        width=line_width
                    )

                # TEXT
                elif kind == "text":

                    text = primitive["text"]

                    x, y = transform(
                        primitive["position"]
                    )

                    font_size = max(
                        1,
                        round(
                            primitive.get("height", 3.5)
                            * scale * S
                        )
                    )

                    font = getFont(font_size)

                    bbox = font.getbbox(text)

                    text_width = max(
                        1,
                        bbox[2] - bbox[0]
                    )

                    text_height = max(
                        1,
                        bbox[3] - bbox[1]
                    )

                    alignment = primitive.get(
                        "alignment",
                        "left"
                    )

                    if alignment == "center":
                        offset_x = -text_width / 2

                    elif alignment == "right":
                        offset_x = -text_width

                    else:
                        offset_x = 0

                    # ---------------------------------
                    # TIGHT TEXT LAYER
                    # ---------------------------------

                    padding = 4

                    text_layer = Image.new(
                        "RGBA",
                        (
                            text_width + padding * 2,
                            text_height + padding * 2
                        ),
                        (0, 0, 0, 0)
                    )

                    text_draw = ImageDraw.Draw(
                        text_layer
                    )

                    text_draw.text(
                        (
                            padding - bbox[0],
                            padding - bbox[1]
                        ),
                        text,
                        font=font,
                        fill=color
                    )

                    # ---------------------------------
                    # POSITION TEXT
                    # ---------------------------------

                    center_x = (
                        x
                        + offset_x
                        + text_width / 2
                    )

                    center_y = y

                    rotation = primitive.get(
                        "rotation",
                        0
                    )

                    if rotation != 0:

                        text_layer = text_layer.rotate(
                            rotation,
                            resample=Image.Resampling.BICUBIC,
                            expand=True
                        )

                    # Preserve text centre during rotation.
                    paste_x = round(
                        center_x - text_layer.width / 2
                    )

                    paste_y = round(
                        center_y - text_layer.height / 2
                    )

                    image.paste(
                        text_layer,
                        (paste_x, paste_y),
                        text_layer
                    )

        # -----------------------------------------
        # DOWNSAMPLE
        # -----------------------------------------

        if S > 1:

            image = image.resize(
                (width, height),
                Image.Resampling.LANCZOS
            )

        # -----------------------------------------
        # UPDATE EXISTING CANVAS IMAGE
        # -----------------------------------------

        photo = ImageTk.PhotoImage(image)

        if render_state["image_item"] is None:

            render_state["image_item"] = canvas.create_image(
                0,
                0,
                image=photo,
                anchor="nw"
            )

        else:

            canvas.itemconfig(
                render_state["image_item"],
                image=photo
            )

        render_state["photo"] = photo

        canvas.preview_image = photo

        update_readout()


    # -------------------------------------------------
    # SCHEDULED RENDERING
    # -------------------------------------------------

    def request_render():

        # Schedule a quick preview if one isn't
        # already waiting in the event queue.

        if render_state["preview_job"] is None:

            render_state["preview_job"] = canvas.after(
                16,
                render_interactive
            )

        # Reset the final-quality render timer.

        if render_state["final_job"] is not None:

            canvas.after_cancel(
                render_state["final_job"]
            )

        render_state["final_job"] = canvas.after(
            160,
            render_final
        )

    global _ACTIVE_REDRAW

    _ACTIVE_REDRAW = request_render

    def render_interactive():

        render_state["preview_job"] = None

        render(INTERACTIVE_QUALITY)

    def render_final():

        render_state["final_job"] = None

        render(FINAL_QUALITY)

    # -------------------------------------------------
    # ZOOM
    # -------------------------------------------------

    def zoom_at(event, factor):

        old_zoom = view["zoom"]

        new_zoom = max(
            MIN_ZOOM,
            min(MAX_ZOOM, old_zoom * factor)
        )

        actual_factor = new_zoom / old_zoom

        if actual_factor == 1:
            return

        margin = 30

        origin_x = margin
        origin_y = canvas.winfo_height() - margin

        view["pan_x"] = (
            event.x - origin_x
            - (event.x - origin_x - view["pan_x"])
            * actual_factor
        )

        view["pan_y"] = (
            event.y - origin_y
            - (event.y - origin_y - view["pan_y"])
            * actual_factor
        )

        view["zoom"] = new_zoom

        view["cursor_x"] = event.x
        view["cursor_y"] = event.y

        update_readout()

        request_render()

    def handle_zoom(event, direction):

        left_button_held = bool(
            event.state & 0x0100
        )

        factor = (
            ZOOM_FACTOR_FAST
            if left_button_held
            else ZOOM_FACTOR
        )

        if direction > 0:
            zoom_at(event, factor)

        else:
            zoom_at(event, 1 / factor)

    def mouse_wheel(event):

        handle_zoom(
            event,
            event.delta
        )

    def linux_zoom_in(event):

        handle_zoom(event, 1)

    def linux_zoom_out(event):

        handle_zoom(event, -1)

    canvas.bind(
        "<MouseWheel>",
        mouse_wheel
    )

    canvas.bind(
        "<Button-4>",
        linux_zoom_in
    )

    canvas.bind(
        "<Button-5>",
        linux_zoom_out
    )

    # -------------------------------------------------
    # CURSOR COORDINATE TRACKING
    # -------------------------------------------------

    def track_cursor(event):

        view["cursor_x"] = event.x
        view["cursor_y"] = event.y

        update_readout()

    canvas.bind(
        "<Motion>",
        track_cursor
    )

    # -----------------------------------------
    # PAN CONTROLS
    # -----------------------------------------

    def start_pan(event):

        view["drag_x"] = event.x
        view["drag_y"] = event.y

        # Indicate that the drawing can be dragged.
        canvas.configure(cursor="fleur")


    def drag_pan(event):

        dx = event.x - view["drag_x"]
        dy = event.y - view["drag_y"]

        view["pan_x"] += dx
        view["pan_y"] += dy

        view["drag_x"] = event.x
        view["drag_y"] = event.y

        view["cursor_x"] = event.x
        view["cursor_y"] = event.y

        update_readout()

        request_render()


    def stop_pan(event):

        canvas.configure(cursor="")


    # Left mouse button: Google Maps-style navigation.
    canvas.bind("<ButtonPress-1>", start_pan)
    canvas.bind("<B1-Motion>", drag_pan)
    canvas.bind("<ButtonRelease-1>", stop_pan)


    # -------------------------------------------------
    # RESIZE
    # -------------------------------------------------

    def on_resize(event):

        size = (
            event.width,
            event.height
        )

        if size == render_state["last_size"]:
            return

        render_state["last_size"] = size

        request_render()

    canvas.bind(
        "<Configure>",
        on_resize
    )

    # -------------------------------------------------
    # INITIAL RENDER
    # -------------------------------------------------

    canvas.after(
        50,
        render_final
    )

# ---------------------------------------------------------
# MAIN FILE PREVIEW ROUTER
# ---------------------------------------------------------

def previewFile(path, shape_pane, preview_pane):
    """
    Main entry point for displaying a file.

    Shape List:
        Raw bytes for ordinary files.
        Formatted JSON for valid Drafting structures.

    Preview:
        Interpreted text, image, or 2D drawing.
    """

    clearPreview(shape_pane, preview_pane)

    if not os.path.isfile(path):
        messagebox.showerror(
            "File Error",
            "The selected path is not a file."
        )
        return

    extension = os.path.splitext(path)[1].lower()

    try:

        if extension == ".json":
            previewJSON(path, shape_pane, preview_pane)

        elif extension in {
            ".png", ".jpg", ".jpeg", ".gif",
            ".bmp", ".tif", ".tiff", ".webp", ".ico"
        }:
            previewRawData(path, shape_pane)
            previewImage(path, preview_pane)

        else:
            previewRawData(path, shape_pane)
            previewText(path, preview_pane)

    except OSError as error:
        clearPreview(shape_pane, preview_pane)

        messagebox.showerror(
            "File Error",
            f"Unable to preview file:\n{error}"
        )