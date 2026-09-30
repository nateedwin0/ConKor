import os

def populate(path, filetree):

    # Clear the existing file tree
    for item in filetree.get_children():
        filetree.delete(item)

    # Get everything inside the directory
    contents = os.listdir(path)

    # Populate the file tree
    for item in contents:

        # Get the full path of the item
        item_path = os.path.join(path, item)

        # Check whether it is a directory
        if os.path.isdir(item_path):

            # Add directory to the tree
            filetree.insert(
                "",
                "end",
                text=item,
                values=("Directory",)
            )

        else:

            # Add file to the tree
            filetree.insert(
                "",
                "end",
                text=item,
                values=("File",)
            )

#Function to open files and directories, populating the file tree and shape list panes.
def openPath(path, filetree, shapelist):

    # Ensure the path exists
    if os.path.exists(path):

        # Check if the path is a directory or a file.
        if os.path.isdir(path):

            #Populate the file tree
            populate(filetree)


        elif os.path.isfile(path):

            #populate the file tree
            populate(path, filetree)

            #populate the shape list
            populate(shapelist)

        


def saveFile(path):
def saveAs(path):