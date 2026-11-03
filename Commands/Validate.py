
import math


def validate(obj):
    """
    Verify that an object adheres to the House Drafter JSON standard.

    Currently supports 2D objects and the following primitives:
        point, line, polyline, circle, arc, polygon, text.

    All dimensional measurements must be expressed in millimetres (mm).
    Angles must be expressed in degrees.

    Returns:
        (bool, list): Whether the object is valid and any errors found.
    """

    errors = []

    # Helper: safely check whether a value is a finite number.
    def valid_number(value):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return False

        try:
            return math.isfinite(value)
        except (OverflowError, TypeError, ValueError):
            return False

    # 1. Verify the top-level structure.
    if not isinstance(obj, dict):
        return False, ["Object must be a dictionary."]

    required_keys = {"id", "dimension", "units", "primitives"}

    missing_keys = required_keys - obj.keys()
    extra_keys = obj.keys() - required_keys

    if missing_keys:
        errors.append(f"Missing top-level keys: {sorted(missing_keys)}")

    if extra_keys:
        errors.append(f"Unexpected top-level keys: {sorted(extra_keys)}")

    if missing_keys:
        return False, errors

    # 2. Validate the unique ID.
    if not isinstance(obj["id"], str) or not obj["id"].strip():
        errors.append("'id' must be a non-empty string.")

    # 3. Validate dimensionality.
    if type(obj["dimension"]) is not int or obj["dimension"] != 2:
        errors.append("'dimension' must be the integer 2 for now.")

    # 4. Validate units.
    if obj["units"] != "mm":
        errors.append("'units' must be 'mm' (millimetres) for now.")

    # 5. Validate the primitives list.
    primitives = obj["primitives"]

    if not isinstance(primitives, list):
        errors.append("'primitives' must be a list.")
        return False, errors

    # Helper: validate a 2D coordinate pair.
    def valid_point(value):
        return (
            isinstance(value, list)
            and len(value) == 2
            and all(valid_number(n) for n in value)
        )

    # Helper: validate hexadecimal RGB colours.
    def valid_color(value):
        if not isinstance(value, str):
            return False

        if len(value) != 7 or not value.startswith("#"):
            return False

        try:
            int(value[1:], 16)
            return True

        except ValueError:
            return False

    # 6. Primitive schemas.
    primitive_schemas = {
        "point": {"position", "color"},
        "line": {"start", "end", "color"},
        "polyline": {"points", "color"},
        "circle": {"center", "radius", "color"},
        "arc": {
            "center", "radius", "start_angle", "end_angle", "color"
        },
        "polygon": {"points", "color"},
        "text": {"position", "text", "color"}
    }

    for index, primitive in enumerate(primitives):

        prefix = f"Primitive {index}"

        if not isinstance(primitive, dict):
            errors.append(f"{prefix} must be a dictionary.")
            continue

        # Validate primitive type.
        primitive_type = primitive.get("type")

        if (
            not isinstance(primitive_type, str)
            or primitive_type not in primitive_schemas
        ):
            errors.append(
                f"{prefix} has unknown type: {primitive_type!r}."
            )
            continue

        # Check required properties.
        required = primitive_schemas[primitive_type] | {"type"}
        missing = required - primitive.keys()

        if missing:
            errors.append(
                f"{prefix} ({primitive_type}) is missing: "
                f"{sorted(missing)}"
            )
            continue

        # Validate optional lineweight (millimetres).
        if "lineweight" in primitive:

            lineweight = primitive["lineweight"]

            if not valid_number(lineweight) or lineweight <= 0:
                errors.append(
                    f"{prefix}: 'lineweight' must be a positive finite number "
                    "representing millimetres."
                )

        # Validate primitive colour.
        if not valid_color(primitive["color"]):
            errors.append(
                f"{prefix}: 'color' must be a valid hexadecimal RGB colour "
                "in the format '#RRGGBB'."
            )

        # Coordinate validation.
        coordinate_keys = {
            "point": ["position"],
            "line": ["start", "end"],
            "polyline": ["points"],
            "circle": ["center"],
            "arc": ["center"],
            "polygon": ["points"],
            "text": ["position"]
        }

        for key in coordinate_keys[primitive_type]:

            value = primitive[key]

            if key == "points":

                minimum = 3 if primitive_type == "polygon" else 2

                if (
                    not isinstance(value, list)
                    or len(value) < minimum
                    or not all(valid_point(p) for p in value)
                ):
                    errors.append(
                        f"{prefix}: '{key}' must contain at least "
                        f"{minimum} valid 2D coordinate pairs."
                    )

            elif not valid_point(value):
                errors.append(
                    f"{prefix}: '{key}' must be [x, y] "
                    "with finite numeric coordinates."
                )

        # Validate radius (millimetres).
        if primitive_type in {"circle", "arc"}:

            radius = primitive["radius"]

            if not valid_number(radius) or radius <= 0:
                errors.append(
                    f"{prefix}: 'radius' must be a positive finite number "
                    "representing millimetres."
                )

        # Validate arc angles (degrees).
        if primitive_type == "arc":

            for key in ("start_angle", "end_angle"):

                angle = primitive[key]

                if not valid_number(angle):
                    errors.append(
                        f"{prefix}: '{key}' must be a finite number "
                        "representing degrees."
                    )

        # Validate text.
        if primitive_type == "text":

            text = primitive["text"]

            if not isinstance(text, str):
                errors.append(
                    f"{prefix}: 'text' must be a string."
                )

            elif not text.strip():
                errors.append(
                    f"{prefix}: 'text' cannot be empty or whitespace-only."
                )

            # Text height (millimetres).
            height = primitive.get("height", 3.5)

            if not valid_number(height) or height <= 0:
                errors.append(
                    f"{prefix}: 'height' must be a positive finite number "
                    "representing millimetres."
                )

            # Text rotation (degrees).
            rotation = primitive.get("rotation", 0)

            if not valid_number(rotation):
                errors.append(
                    f"{prefix}: 'rotation' must be a finite number."
                )

            # Text alignment.
            alignment = primitive.get("alignment", "left")

            if (
                not isinstance(alignment, str)
                or alignment not in {"left", "center", "right"}
            ):
                errors.append(
                    f"{prefix}: 'alignment' must be "
                    "'left', 'center', or 'right'."
                )

        # Reject zero-length lines.
        if primitive_type == "line":

            start = primitive["start"]
            end = primitive["end"]

            if valid_point(start) and valid_point(end) and start == end:
                errors.append(
                    f"{prefix}: line start and end cannot be identical."
                )

    return len(errors) == 0, errors