def exportJsonToPDF(argument_path):
    """
    Validate a Drafting JSON structure and export it
    as a vector-based 2D PDF drawing.

    Supported primitives:
        point
        line
        polyline
        polygon
        circle
        arc

    Returns:
        (True, output_path) on success.
        (False, error_message) on failure.
    """

    import os
    import json
    from Validate import validate

    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.units import mm

    # -----------------------------------------------------
    # 1. OPEN AND READ JSON
    # -----------------------------------------------------

    argument_path = os.path.abspath(argument_path)

    if not os.path.isfile(argument_path):
        return False, "The specified JSON file does not exist."

    try:
        with open(argument_path, "r", encoding="utf-8") as file:
            data = json.load(file)

    except (json.JSONDecodeError, OSError) as error:
        return False, f"Unable to read JSON file: {error}"

    # -----------------------------------------------------
    # 2. VALIDATE STRUCTURE
    # -----------------------------------------------------

    try:
        valid, errors = validate(data)

    except Exception as error:
        return False, f"Validation failed: {error}"

    if not valid:
        return False, (
            "Invalid Drafting structure:\n"
            + "\n".join(errors)
        )

    # -----------------------------------------------------
    # 3. CHECK DIMENSIONALITY
    # -----------------------------------------------------

    if data["dimension"] != 2:
        return False, "PDF export currently supports 2D structures only."

    primitives = data["primitives"]

    # -----------------------------------------------------
    # 4. DETERMINE DRAWING BOUNDARIES
    # -----------------------------------------------------

    points = []

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

    if not points:
        return False, "The drawing contains no supported geometry."

    min_x = min(point[0] for point in points)
    max_x = max(point[0] for point in points)

    min_y = min(point[1] for point in points)
    max_y = max(point[1] for point in points)

    drawing_width = max(max_x - min_x, 1)
    drawing_height = max(max_y - min_y, 1)

    # -----------------------------------------------------
    # 5. CREATE PDF DOCUMENT
    # -----------------------------------------------------

    output_path = os.path.splitext(argument_path)[0] + ".pdf"

    page_width, page_height = landscape(A4)

    try:

        pdf = canvas.Canvas(
            output_path,
            pagesize=(page_width, page_height)
        )

        pdf.setTitle(os.path.basename(argument_path))
        pdf.setAuthor("House Drafter")

        # -------------------------------------------------
        # 6. CALCULATE DRAWING SCALE
        # -------------------------------------------------

        margin = 20 * mm

        available_width = page_width - margin * 2
        available_height = page_height - margin * 2

        scale = min(
            available_width / drawing_width,
            available_height / drawing_height
        )

        # Centre the drawing on the page.
        rendered_width = drawing_width * scale
        rendered_height = drawing_height * scale

        offset_x = (page_width - rendered_width) / 2
        offset_y = (page_height - rendered_height) / 2

        # -------------------------------------------------
        # 7. COORDINATE TRANSFORMATION
        # -------------------------------------------------

        def transform(point):
            """
            Convert drafting coordinates into PDF points.

            PDF coordinates already increase upwards,
            so no Y-axis inversion is required.
            """

            x, y = point

            pdf_x = offset_x + (x - min_x) * scale
            pdf_y = offset_y + (y - min_y) * scale

            return pdf_x, pdf_y

        # -------------------------------------------------
        # 8. SET DRAWING STYLE
        # -------------------------------------------------

        pdf.setStrokeColorRGB(0, 0, 0)
        pdf.setFillColorRGB(0, 0, 0)

        # Default line thickness: 0.25 mm.
        pdf.setLineWidth(0.25 * mm)

        # -------------------------------------------------
        # 9. RENDER PRIMITIVES
        # -------------------------------------------------

        for primitive in primitives:

            kind = primitive["type"]

            # ---------------------------------------------
            # POINT
            # ---------------------------------------------

            if kind == "point":

                x, y = transform(primitive["position"])

                pdf.circle(
                    x,
                    y,
                    1.0 * mm,
                    stroke=1,
                    fill=1
                )

            # ---------------------------------------------
            # LINE
            # ---------------------------------------------

            elif kind == "line":

                x1, y1 = transform(primitive["start"])
                x2, y2 = transform(primitive["end"])

                pdf.line(
                    x1, y1,
                    x2, y2
                )

            # ---------------------------------------------
            # POLYLINE
            # ---------------------------------------------

            elif kind == "polyline":

                coordinates = [
                    transform(point)
                    for point in primitive["points"]
                ]

                path = pdf.beginPath()

                path.moveTo(*coordinates[0])

                for x, y in coordinates[1:]:
                    path.lineTo(x, y)

                pdf.drawPath(path)

            # ---------------------------------------------
            # POLYGON
            # ---------------------------------------------

            elif kind == "polygon":

                coordinates = [
                    transform(point)
                    for point in primitive["points"]
                ]

                path = pdf.beginPath()

                path.moveTo(*coordinates[0])

                for x, y in coordinates[1:]:
                    path.lineTo(x, y)

                path.close()

                pdf.drawPath(
                    path,
                    stroke=1,
                    fill=0
                )

            # ---------------------------------------------
            # CIRCLE
            # ---------------------------------------------

            elif kind == "circle":

                cx, cy = transform(primitive["center"])

                radius = primitive["radius"] * scale

                pdf.circle(
                    cx,
                    cy,
                    radius,
                    stroke=1,
                    fill=0
                )

            # ---------------------------------------------
            # ARC
            # ---------------------------------------------

            elif kind == "arc":

                cx, cy = transform(primitive["center"])

                radius = primitive["radius"] * scale

                start = primitive["start_angle"]
                end = primitive["end_angle"]

                pdf.arc(
                    cx - radius,
                    cy - radius,
                    cx + radius,
                    cy + radius,
                    startAng=start,
                    extent=end - start
                )

        # -------------------------------------------------
        # 10. EXPORT PDF
        # -------------------------------------------------

        pdf.showPage()
        pdf.save()

        return True, output_path

    except Exception as error:

        return False, f"PDF export failed: {error}"