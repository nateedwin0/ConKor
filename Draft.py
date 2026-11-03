######################################### Draft.py #########################################

import sys
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from Commands import Preview, Save, Export

# ---------------------------------------------------------
# APPLICATION STATE
# ---------------------------------------------------------

Shapes = {}
CurrentFile = ""

# ---------------------------------------------------------
# APPLICATION WINDOW
# ---------------------------------------------------------

root = tk.Tk()
root.title("House Drafter")
root.geometry("1200x700")

# ---------------------------------------------------------
# MAIN PANE LAYOUT
# ---------------------------------------------------------

main_panes = ttk.PanedWindow(
    root,
    orient="horizontal"
)

main_panes.pack(fill="both", expand=True)


# ---------------------------------------------------------
# FILE EXPLORER PANE
# ---------------------------------------------------------

file_pane = ttk.Frame(main_panes)
main_panes.add(file_pane, weight=1)

file_label = ttk.Label(
    file_pane,
    text="File Explorer"
)

file_label.pack(anchor="w", padx=10, pady=10)

file_tree = ttk.Treeview(file_pane)

file_tree.pack(
    fill="both",
    expand=True,
    padx=5,
    pady=5
)

# ---------------------------------------------------------
# SHAPE LIST PANE
# ---------------------------------------------------------

shape_pane = ttk.Frame(main_panes)
main_panes.add(shape_pane, weight=1)

shape_label = ttk.Label(
    shape_pane,
    text="Data"
)

shape_label.pack(anchor="w", padx=10, pady=10)

# Dynamic container for raw file data or formatted JSON.
shape_content = ttk.Frame(shape_pane)

shape_content.pack(
    fill="both",
    expand=True,
    padx=5,
    pady=5
)

# ---------------------------------------------------------
# PREVIEW PANE
# ---------------------------------------------------------

preview_pane = ttk.Frame(main_panes)
main_panes.add(preview_pane, weight=3)

preview_label = ttk.Label(
    preview_pane,
    text="Preview"
)

preview_label.pack(anchor="w", padx=10, pady=10)

# Dynamic container for interpreted content or drawings.
preview_content = ttk.Frame(preview_pane)

preview_content.pack(
    fill="both",
    expand=True,
    padx=5,
    pady=5
)

# ---------------------------------------------------------
# PANE MANAGEMENT
# ---------------------------------------------------------

def togglePane(pane):
    """
    Toggle the visibility of a pane.
    """

    if str(pane) in main_panes.panes():
        main_panes.forget(pane)

    else:
        restorePane(pane)

def restorePane(pane):
    """
    Restore a pane to its original position.
    """

    current_panes = main_panes.panes()

    # Don't restore an already visible pane.
    if str(pane) in current_panes:
        return

    # Original pane ordering.
    pane_order = [
        file_pane,
        shape_pane,
        preview_pane
    ]

    # Find the pane's intended position.
    target_index = pane_order.index(pane)

    # Count visible panes that should appear before this pane.
    insert_index = sum(
        1 for existing_pane in pane_order[:target_index]
        if str(existing_pane) in current_panes
    )

    # Restore pane with its original weight.
    weights = {
        file_pane: 1,
        shape_pane: 1,
        preview_pane: 3
    }

    main_panes.insert(
        insert_index,
        pane,
        weight=weights[pane]
    )

def restoreDefaultLayout():
    """
    Restore all panes and their default proportions.
    """

    restorePane(file_pane)
    restorePane(shape_pane)
    restorePane(preview_pane)

    root.update_idletasks()

    width = main_panes.winfo_width()

    if width > 0:
        main_panes.sashpos(0, int(width * 0.20))
        main_panes.sashpos(1, int(width * 0.40))
        
# ---------------------------------------------------------
# INITIAL PANE CONTENT
# ---------------------------------------------------------

# Shapes pane placeholder
shape_placeholder = ttk.Label(
    shape_content,
    text="No file currently open.\n\nOpen a file to view is data.",
    anchor="center",
    justify="center"
)

shape_placeholder.pack(
    fill="both",
    expand=True
)

# Preview pane placeholder
preview_placeholder = ttk.Label(
    preview_content,
    text="Open a file to begin drafting \n\n(Ctrl+O).",
    anchor="center",
    justify="center"
)

preview_placeholder.pack(
    fill="both",
    expand=True
)

# ---------------------------------------------------------
# FILE EXPLORER FUNCTIONS
# ---------------------------------------------------------

def populateFileTree(path):
    """
    Populate the File Explorer with the contents
    of a selected directory.
    """

    file_tree.delete(*file_tree.get_children())

    path = os.path.abspath(path)

    try:
        entries = sorted(
            os.listdir(path),
            key=lambda item: (
                not os.path.isdir(os.path.join(path, item)),
                item.lower()
            )
        )

        for entry in entries:

            entry_path = os.path.join(path, entry)

            file_type = (
                "Directory" if os.path.isdir(entry_path)
                else "File"
            )

            file_tree.insert(
                "",
                "end",
                text=entry,
                values=(entry_path, file_type)
            )

    except OSError as error:
        messagebox.showerror(
            "Directory Error",
            f"Unable to read directory:\n{error}"
        )


def openDirectory():
    """
    Select a directory and populate the File Explorer.
    """

    path = filedialog.askdirectory(
        title="Open Directory"
    )

    if not path:
        return

    populateFileTree(path)


# ---------------------------------------------------------
# FILE OPENING
# ---------------------------------------------------------

def openFile(path=None):
    """
    Open a file and pass it to Preview.py.

    The Preview module determines how the file
    should be interpreted and displayed.
    """

    global CurrentFile

    if path is None:

        path = filedialog.askopenfilename(
            title="Open File",
            filetypes=[
                ("All Files", "*.*"),
                ("Drafting Files", "*.json"),
                ("Text Files", "*.txt"),
                ("Images", "*.png *.jpg *.jpeg *.bmp *.gif")
            ]
        )

    if not path:
        return

    path = os.path.abspath(path)

    if not os.path.isfile(path):
        messagebox.showerror(
            "File Error",
            "The selected path is not a file."
        )
        return

    CurrentFile = path

    # Update the File Explorer to show the file's directory.
    populateFileTree(os.path.dirname(path))

    # Delegate file interpretation to Preview.py.
    Preview.previewFile(
        CurrentFile,
        shape_content,
        preview_content
    )

def onFileTreeDoubleClick(event):
    """
    Open the selected file or navigate into a directory.
    """

    selected = file_tree.selection()

    if not selected:
        return

    item = selected[0]

    values = file_tree.item(item, "values")

    if not values:
        return

    selected_path = values[0]

    if os.path.isdir(selected_path):

        populateFileTree(selected_path)

    elif os.path.isfile(selected_path):

        openFile(selected_path)

# ---------------------------------------------------------
# SAVE FUNCTIONS
# ---------------------------------------------------------

def getCurrentContents():
    """
    Retrieve the editable content currently displayed
    in the Preview pane, or formatted JSON in Shape List.
    """

    if hasattr(preview_content, "text_widget"):
        return preview_content.text_widget.get("1.0", "end-1c")

    if hasattr(shape_content, "text_widget"):
        return shape_content.text_widget.get("1.0", "end-1c")

    return ""

def saveFile():
    """
    Save the current file.

    Uses the existing Commands module.
    """

    if not CurrentFile:
        messagebox.showwarning(
            "Save",
            "No file is currently open. Use Save As."
        )
        return

    contents = getCurrentContents()

    success, result = Save.saveFile(
        Shapes,
        contents,
        CurrentFile
    )

    if success:
        messagebox.showinfo("Save", result)
    else:
        messagebox.showerror("Save Error", result)

def saveAs():
    """
    Save the current content to a different path.
    """

    global CurrentFile

    path = filedialog.asksaveasfilename(
        title="Save As",
        defaultextension=".json",
        filetypes=[
            ("Drafting Files", "*.json"),
            ("Text Files", "*.txt"),
            ("All Files", "*.*")
        ]
    )

    if not path:
        return

    contents = getCurrentContents()

    success, result = Save.saveFileToPath(
        path,
        Shapes,
        contents
    )

    if success:
        CurrentFile = os.path.abspath(path)
        messagebox.showinfo("Save As", result)
    else:
        messagebox.showerror("Save Error", result)

# ---------------------------------------------------------
# MENU BAR
# ---------------------------------------------------------

menubar = tk.Menu(root)

# ---------------------------------------------------------
# FILE MENU
# ---------------------------------------------------------

file_menu = tk.Menu(
    menubar,
    tearoff=0
)

file_menu.add_command(
    label="Open File",
    accelerator="Ctrl+O",
    command=openFile
)

file_menu.add_command(
    label="Open Folder",
    accelerator="Ctrl+Shift+O",
    command=openDirectory
)

file_menu.add_separator()

file_menu.add_command(
    label="Save",
    accelerator="Ctrl+S",
    command=saveFile
)

file_menu.add_command(
    label="Save As",
    accelerator="Ctrl+Shift+S",
    command=saveAs
)

menubar.add_cascade(
    label="File",
    menu=file_menu
)

# ---------------------------------------------------------
# SETTINGS MENU
# ---------------------------------------------------------

settings_menu = tk.Menu(
    menubar,
    tearoff=0
)

settings_menu.add_command(
    label="File Explorer",
    accelerator="Ctrl+F",
    command=lambda: togglePane(file_pane)
)

settings_menu.add_command(
    label="Data Pane",
    accelerator="Ctrl+D",
    command=lambda: togglePane(shape_pane)
)

settings_menu.add_command(
    label="Preview Pane",
    accelerator="Ctrl+E",
    command=lambda: togglePane(preview_pane)
)

settings_menu.add_separator()

settings_menu.add_command(
    label="Restore Default Layout",
    accelerator="Ctrl+R",
    command=restoreDefaultLayout
)

menubar.add_cascade(
    label="Settings",
    menu=settings_menu
)

# -----------------------------------------
# GRID VISIBILITY SETTING
# -----------------------------------------

show_grid = tk.BooleanVar(
    root,
    value=True
)

def toggleGrid():

    Preview.setGridVisible(
        show_grid.get()
    )

settings_menu.add_checkbutton(
    label="Show Grid",
    variable=show_grid,
    command=toggleGrid
)

# ---------------------------------------------------------
# KEYBOARD SHORTCUTS
# ---------------------------------------------------------

# File operations
root.bind_all("<Control-o>", lambda event: openFile())
root.bind_all("<Control-Shift-O>", lambda event: openDirectory())
root.bind_all("<Control-s>", lambda event: saveFile())
root.bind_all("<Control-Shift-S>", lambda event: saveAs())

# Workspace management
root.bind_all("<Control-f>", lambda event: togglePane(file_pane))
root.bind_all("<Control-d>", lambda event: togglePane(shape_pane))
root.bind_all("<Control-e>", lambda event: togglePane(preview_pane))
root.bind_all("<Control-r>", lambda event: restoreDefaultLayout())


# Attach menu bar to application.
root.config(menu=menubar)

# ---------------------------------------------------------
# FILE EXPLORER EVENTS
# ---------------------------------------------------------

file_tree.bind(
    "<Double-1>",
    onFileTreeDoubleClick
)


# ---------------------------------------------------------
# COMMAND LINE ARGUMENTS
# ---------------------------------------------------------

# Parse arguments after the application has been initialized.
arguments = sys.argv[1:]

if len(arguments) >= 2:

    command = arguments[0]
    argument_path = arguments[1]

    if command == "open":

        if os.path.isfile(argument_path):
            root.after(
                100,
                lambda: openFile(argument_path)
            )

        elif os.path.isdir(argument_path):
            root.after(
                100,
                lambda: populateFileTree(argument_path)
            )

    elif command == "export":

        Export.exportJsonToPDF(argument_path)
        root.destroy()
        sys.exit(0)


# ---------------------------------------------------------
# APPLICATION MAIN LOOP
# ---------------------------------------------------------

root.mainloop()