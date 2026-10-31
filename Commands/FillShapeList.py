#A Function to fill the Shape List pane
def fill(path): 

    #Access the given path.
    with open(path, "r") as file:

        #Check if the file is JSON.
        if path.lower().endswith(".json"):

            #Extract the JSON from the file
            shapes = json.load(file)

            #Validate the structure of the JSON
            validate(shapes)

            #Check the dimensions of the file (2d/3d)
            if shapes["dimension"] == 2:

                #Parse the JSON to adhere to the defined possible shapes


                #Return the verified dictionary of shapes
                return shapes

            #TODO - Add in three dimensional support
            else:

                #Signal invalid json architecture
                return False

        else:

            #Return the file contents as plain text.
            return file.read()
