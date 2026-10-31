import messagebox
import Save

def closeApplication(UnsavedChanges):
    """
    Gracefully close the application.

    If there are unsaved changes, ask the user whether to save.
    """

    global root

    # Check whether the project has unsaved changes.
    if UnsavedChanges:
        response = messagebox.askyesnocancel(
            "Unsaved Changes",
            "Would you like to save your changes before exiting?"
        )

        # Cancel closing.
        if response is None:
            return

        # Save before closing.
        if response is True:
            success, message = Save.saveFile()

            if not success:
                messagebox.showerror("Save Failed", message)
                return

    # Close the Tkinter application.
    root.destroy()