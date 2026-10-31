
import json
import os
import tkinter as tk
from tkinter import ttk, messagebox
from Commands import Validate
from PIL import Image, ImageTk, ImageDraw, ImageFont

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
    Render a valid 2D drafting structure.

    Features:
        - 3x supersampling anti-aliasing
        - LANCZOS downsampling
        - Automatic fit-to-view
        - Mouse-wheel zoom
        - Cursor-centred zoom
        - Middle/right mouse drag to pan
        - Automatic redraw when resized

    Supported primitives:
        point, line, polyline, polygon, circle, arc
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

    # -----------------------------------------
    # VIEW SETTINGS
    # -----------------------------------------

    view = {
        "zoom": 1.0,
        "pan_x": 0.0,
        "pan_y": 0.0,
        "drag_x": 0.0,
        "drag_y": 0.0
    }

    MIN_ZOOM = 0.1
    MAX_ZOOM = 20.0

    ZOOM_FACTOR = 1.1
    ZOOM_FACTOR_FAST = 1.25

    # Anti-aliasing quality.
    SUPERSAMPLE = 3

    # -----------------------------------------
    # LINEWEIGHT
    # -----------------------------------------

    def getLineWidth(primitive):
        """
        Convert drafting lineweight in millimetres
        into screen pixels.

        Defaults to 0.35 mm.
        """

        lineweight = primitive.get("lineweight", 0.35)

        pixels = lineweight * 96 / 25.4

        return max(1, round(pixels))

    # -----------------------------------------
    # RENDERING
    # -----------------------------------------

    def render(event=None):

        canvas.delete("all")

        width = canvas.winfo_width()
        height = canvas.winfo_height()

        if width <= 1 or height <= 1:
            return

        primitives = data["primitives"]
        points = []

        # Gather coordinates for drawing bounds.
        for primitive in primitives:

            kind = primitive["type"]

            if kind == "point":
                points.append(primitive["position"])

            elif kind == "line":
                points.extend([
                    primitive["start"],
                    primitive["end"]
                ])

            elif kind in ("polyline", "polygon"):
                points.extend(primitive["points"])

            elif kind in ("circle", "arc"):

                cx, cy = primitive["center"]
                radius = primitive["radius"]

                points.extend([
                    [cx - radius, cy - radius],
                    [cx + radius, cy + radius]
                ])

            elif kind == "text":
                points.append(primitive["position"])

        # -------------------------------------
        # CREATE HIGH-RESOLUTION IMAGE
        # -------------------------------------

        S = SUPERSAMPLE

        image = Image.new(
            "RGB",
            (width * S, height * S),
            "white"
        )

        draw = ImageDraw.Draw(image)

        if not points:

            draw.text(
                (width * S / 2, height * S / 2),
                "No drawable geometry",
                fill="black",
                anchor="mm"
            )

        else:

            min_x = min(point[0] for point in points)
            max_x = max(point[0] for point in points)

            min_y = min(point[1] for point in points)
            max_y = max(point[1] for point in points)

            drawing_width = max(max_x - min_x, 1)
            drawing_height = max(max_y - min_y, 1)

            margin = 30

            base_scale = min(
                (width - margin * 2) / drawing_width,
                (height - margin * 2) / drawing_height
            )

            scale = base_scale * view["zoom"]

            # ---------------------------------
            # COORDINATE TRANSFORMATION
            # ---------------------------------

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

            # ---------------------------------
            # DRAW PRIMITIVES
            # ---------------------------------

            for primitive in primitives:

                kind = primitive["type"]
                color = primitive["color"]

                line_width = max(
                    1,
                    getLineWidth(primitive) * S
                )

                # POINT
                if kind == "point":

                    x, y = transform(primitive["position"])

                    radius = 3 * S

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

                    p1 = transform(primitive["start"])
                    p2 = transform(primitive["end"])

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

                        coordinates.append(coordinates[0])

                    draw.line(
                        coordinates,
                        fill=color,
                        width=line_width,
                        joint="curve"
                    )

                # CIRCLE
                elif kind == "circle":

                    cx, cy = transform(primitive["center"])

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

                    cx, cy = transform(primitive["center"])

                    radius = (
                        primitive["radius"] * scale * S
                    )

                    start = primitive["start_angle"]
                    end = primitive["end_angle"]

                    # Convert mathematical angles to
                    # Pillow's screen-coordinate angles.
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

                    x, y = transform(primitive["position"])

                    # Convert drawing-unit text height
                    # into high-resolution screen pixels.
                    font_size = max(
                        1,
                        round(
                            primitive.get("height", 3.5)
                            * scale * S
                        )
                    )

                    # Load a scalable font.
                    try:
                        font = ImageFont.truetype(
                            "arial.ttf",
                            font_size
                        )
                    except OSError:
                        try:
                            font = ImageFont.truetype(
                                "DejaVuSans.ttf",
                                font_size
                            )
                        except OSError:
                            font = ImageFont.load_default()

                    # Measure the text.
                    bbox = font.getbbox(text)

                    text_width = max(1, bbox[2] - bbox[0])
                    text_height = max(1, bbox[3] - bbox[1])

                    # Alignment.
                    alignment = primitive.get(
                        "alignment", "left"
                    )

                    if alignment == "center":
                        offset_x = -text_width / 2

                    elif alignment == "right":
                        offset_x = -text_width

                    else:
                        offset_x = 0

                    # Create a transparent layer.
                    padding = max(text_width, text_height) + 4

                    text_layer = Image.new(
                        "RGBA",
                        (
                            text_width + padding * 2,
                            text_height + padding * 2
                        ),
                        (0, 0, 0, 0)
                    )

                    text_draw = ImageDraw.Draw(text_layer)

                    text_draw.text(
                        (
                            padding + offset_x - bbox[0],
                            padding - text_height / 2 - bbox[1]
                        ),
                        text,
                        font=font,
                        fill=color
                    )

                    # Rotate around the insertion position.
                    rotation = primitive.get("rotation", 0)

                    if rotation != 0:
                        text_layer = text_layer.rotate(
                            rotation,
                            resample=Image.Resampling.BICUBIC,
                            expand=False
                        )

                    # Composite onto the drawing.
                    image.paste(
                        text_layer,
                        (
                            round(x - padding),
                            round(y - padding)
                        ),
                        text_layer
                    )

        # -------------------------------------
        # DOWNSAMPLE FOR ANTI-ALIASING
        # -------------------------------------

        image = image.resize(
            (width, height),
            Image.Resampling.LANCZOS
        )

        photo = ImageTk.PhotoImage(image)

        canvas.create_image(
            0,
            0,
            image=photo,
            anchor="nw"
        )

        # Prevent garbage collection.
        canvas.preview_image = photo

    # -----------------------------------------
    # ZOOM CONTROLS
    # -----------------------------------------

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

        render()

    def mouse_wheel(event):

        if event.delta > 0:
            zoom_at(event, ZOOM_FACTOR)
        else:
            zoom_at(event, 1 / ZOOM_FACTOR)

    def linux_zoom_in(event):
        zoom_at(event, ZOOM_FACTOR)

    def linux_zoom_out(event):
        zoom_at(event, 1 / ZOOM_FACTOR)

    # Windows / macOS.
    canvas.bind("<MouseWheel>", mouse_wheel)

    # Linux.
    canvas.bind("<Button-4>", linux_zoom_in)
    canvas.bind("<Button-5>", linux_zoom_out)

    # -----------------------------------------
    # PAN CONTROLS
    # -----------------------------------------

    def start_pan(event):

        view["drag_x"] = event.x
        view["drag_y"] = event.y

    def drag_pan(event):

        dx = event.x - view["drag_x"]
        dy = event.y - view["drag_y"]

        view["pan_x"] += dx
        view["pan_y"] += dy

        view["drag_x"] = event.x
        view["drag_y"] = event.y

        render()

    # Middle mouse button.
    canvas.bind("<ButtonPress-2>", start_pan)
    canvas.bind("<B2-Motion>", drag_pan)

    # Right mouse button.
    canvas.bind("<ButtonPress-3>", start_pan)
    canvas.bind("<B3-Motion>", drag_pan)

    # Redraw when resized.
    canvas.bind("<Configure>", render)

    render()

    # -----------------------------------------
    # ZOOM CONTROLS
    # -----------------------------------------

    def zoom_at(event, factor):
        """
        Zoom towards or away from the cursor.

        Preserves the exact drafting location beneath
        the mouse cursor.
        """

        old_zoom = view["zoom"]

        new_zoom = max(
            MIN_ZOOM,
            min(MAX_ZOOM, old_zoom * factor)
        )

        actual_factor = new_zoom / old_zoom

        if actual_factor == 1:
            return

        # Match the coordinate origins used by transform().
        margin = 30

        origin_x = margin
        origin_y = canvas.winfo_height() - margin

        # Preserve the cursor's position relative to
        # the actual drawing origin.
        view["pan_x"] = (
            event.x - origin_x
            - (event.x - origin_x - view["pan_x"]) * actual_factor
        )

        view["pan_y"] = (
            event.y - origin_y
            - (event.y - origin_y - view["pan_y"]) * actual_factor
        )

        view["zoom"] = new_zoom

        render()

    def handle_zoom(event, direction):
        """
        Handle mouse-wheel zoom.

        Normal scrolling:
            Standard zoom speed.

        Left mouse button held:
            Faster zoom speed.
        """

        # Check whether the left mouse button is held.
        left_button_held = bool(event.state & 0x0100)

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
        # Windows / macOS
        handle_zoom(event, event.delta)

    def linux_zoom_in(event):
        # Linux scroll up
        handle_zoom(event, 1)


    def linux_zoom_out(event):
        # Linux scroll down
        handle_zoom(event, -1)

    # Windows / macOS
    canvas.bind("<MouseWheel>", mouse_wheel)

    # Linux
    canvas.bind("<Button-4>", linux_zoom_in)
    canvas.bind("<Button-5>", linux_zoom_out)

    # -----------------------------------------
    # PAN CONTROLS
    # -----------------------------------------

    def start_pan(event):
        view["drag_x"] = event.x
        view["drag_y"] = event.y

    def drag_pan(event):

        dx = event.x - view["drag_x"]
        dy = event.y - view["drag_y"]

        view["pan_x"] += dx
        view["pan_y"] += dy

        view["drag_x"] = event.x
        view["drag_y"] = event.y

        render()

    # Middle mouse button.
    canvas.bind("<ButtonPress-2>", start_pan)
    canvas.bind("<B2-Motion>", drag_pan)

    # Right mouse button.
    canvas.bind("<ButtonPress-3>", start_pan)
    canvas.bind("<B3-Motion>", drag_pan)

    # Redraw when resized.
    canvas.bind("<Configure>", render)

    render()

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