#########################################Draft.py##########################################
# This script shall serve to implement the draft application, presenting a user interface #
# capable of drawing shapes to a 2d or 3d space at the definition of the user.            #
#                                                                                         #
# Draft shall store these shapes in .json files coresponding to use draftings.            #
#                                                                                         #
# Draft shall be capable of creating, retrieving, updating, or deleting user created      #
# drafts, either by command line arguments, or through its GUI.                           #
#                                                                                         #
# Spaces within which drafts exist shall be denominated by units of the users choosing.   #
###########################################################################################
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import Commands

#Define a dictionary to hold shapes
Shapes = {}

#Define available command line args
Args = [
    "open",
    "export"
]

#If command line arguments are present, parse them, execute them.
if sys.argv:

    #Check arguments against all available options.
    for i, arg in enumerate(sys.argv):

        #Open a file/directory in the editor.
        if arg == "open":
            openPath(Args[i+1])

        #Convert a json draft to a pdf.
        if arg == "export":
            exportJsonToPDF(Args[i+1])

#Else, initialise the GUI for user interaction.
root = tk.Tk() 
root.title("House Drafter") 
root.geometry("1200x700")

#Divide the screen into three panes
main_panes = ttk.PanedWindow(root, orient="horizontal") 
main_panes.pack(fill="both", expand=True)

#File explorer pane
file_pane = ttk.Frame(main_panes) 
main_panes.add(file_pane, weight=1) 
file_label = ttk.Label(file_pane, text="File Explorer") 
file_label.pack(anchor="w", padx=10, pady=10)

file_tree = ttk.Treeview( file_pane ) 
file_tree.pack(fill="both", expand=True, padx=5, pady=5)

#Shape list pane
shape_pane = ttk.Frame(main_panes) 
main_panes.add(shape_pane, weight=1) 
shape_label = ttk.Label(shape_pane, text="Shapes") 
shape_label.pack(anchor="w", padx=10, pady=10)

shape_list = tk.Listbox(shape_pane) 
shape_list.pack(fill="both", expand=True, padx=5, pady=5)

#Preview pane
preview_pane = ttk.Frame(main_panes)
main_panes.add(preview_pane, weight=3)
preview_label = ttk.Label(preview_pane, text="Preview")
preview_label.pack( anchor="w", padx=10, pady=10 )

preview_canvas = tk.Canvas(preview_pane, background="white") 
preview_canvas.pack(fill="both", expand=True, padx=5, pady=5)

#Add a top tool bar containing Open, Save, and Save As buttons. 
toolbar = ttk.Frame(root) 
toolbar.pack( side="top", fill="x" ) 

open_button = ttk.Button(toolbar, text="Open", command=openPath) 
open_button.pack( side="left", padx=5, pady=5 ) 

save_button = ttk.Button(toolbar, text="Save", command=saveFile) 
save_button.pack( side="left", padx=5, pady=5 ) 

save_as_button = ttk.Button(toolbar, text="Save As", command=saveAs) 
save_as_button.pack(side="left", padx=5, pady=5)

#Display the GUI for usage
root.mainloop()