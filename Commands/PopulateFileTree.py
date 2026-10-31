import os
from tkinter import messagebox

def populate(path, filetree):
    """
    Populate the file explorer with the contents of a directory.
    """

    # Clear the existing file tree.
    for item in filetree.get_children():
        filetree.delete(item)

    # Configure columns to hold file information.
    filetree["columns"] = ("path", "type")
    filetree.heading("#0", text="Name")
    filetree.heading("path", text="Path")
    filetree.heading("type", text="Type")

    filetree.column("#0", width=150)
    filetree.column("path", width=250)
    filetree.column("type", width=80)

    try:
        contents = sorted(
            os.listdir(path),
            key=lambda item: (
                not os.path.isdir(os.path.join(path, item)),
                item.lower()
            )
        )

        for item in contents:

            item_path = os.path.join(path, item)

            if os.path.isdir(item_path):
                file_type = "Directory"
            else:
                file_type = os.path.splitext(item)[1].lower() or "File"

            filetree.insert(
                "",
                "end",
                text=item,
                values=(item_path, file_type)
            )

    except OSError as error:
        messagebox.showerror(
            "Directory Error",
            f"Unable to read directory:\n{error}"
        )