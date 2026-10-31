import os
import json
import shutil
from Config import Supported

def saveFile(project_data, file_contents, path=None):
    """
    Save the current file to its existing path.

    Supports JSON project data, text/code files, and images.

    Returns:
        (bool, str): Success status and a message.
    """

    global CurrentFile

    # Use the current file path if none is provided.
    if path is None:
        path = CurrentFile

    if not path:
        return False, "No file path provided. Use Save As first."

    extension = os.path.splitext(path)[1].lower()

    try:
        # Save JSON project data.
        if extension == ".json":
            with open(path, "w", encoding="utf-8") as file:
                json.dump(project_data, file, indent=4)

        # Save text and source-code files.
        elif extension in Supported.TEXT_EXTENSIONS:
            with open(path, "w", encoding="utf-8", newline="") as file:
                file.write(file_contents)

        # Images and other binary files must be copied from
        # their original source unless an image editor provides
        # updated binary data.
        elif extension in Supported.IMAGE_EXTENSIONS:
            if not os.path.isfile(path):
                return False, (
                    "Cannot save this image: no edited image data "
                    "or original file is available."
                )

            # The image is unchanged, so there is nothing to write.
            return True, "Image is unchanged; no save needed."

        else:
            return False, f"Unsupported file type: {extension or '(no extension)'}"

        return True, f"File saved successfully: {path}"

    except (OSError, TypeError, ValueError) as error:
        return False, f"Failed to save file: {error}"

def saveFileToPath(path, project_data, file_contents):
    """
    Save the current content to a specified destination.
    Does not change CurrentFile.
    """

    extension = os.path.splitext(path)[1].lower()

    try:
        if extension == ".json":
            with open(path, "w", encoding="utf-8") as file:
                json.dump(project_data, file, indent=4)

        elif extension in Supported.TEXT_EXTENSIONS:
            with open(path, "w", encoding="utf-8", newline="") as file:
                file.write(file_contents)

        elif extension in Supported.IMAGE_EXTENSIONS:
            if not CurrentFile or not os.path.isfile(CurrentFile):
                return False, "No original image file is available to copy."

            # Avoid copying a file onto itself.
            if os.path.abspath(CurrentFile) == os.path.abspath(path):
                return True, "Image is unchanged; no save needed."

            shutil.copy2(CurrentFile, path)

        else:
            return False, f"Unsupported file type: {extension}"

        return True, f"File saved successfully: {path}"

    except (OSError, TypeError, ValueError) as error:
        return False, f"Failed to save file: {error}"

def saveAs(path):
    """
    Save the current content to a new path and update CurrentFile.

    Returns:
        (bool, str): Success status and a message.
    """

    global CurrentFile

    if not path:
        return False, "No destination path provided."

    extension = os.path.splitext(path)[1].lower()

    # Require an extension so the intended file format is explicit.
    if not extension:
        return False, "Please specify a file extension."

    # Save to the new destination.
    success, message = saveFileToPath(path)

    if success:
        CurrentFile = os.path.abspath(path)

    return success, message