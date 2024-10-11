
from tkinter import filedialog

# Function for opening the 
# file explorer window




def browseFiles():
	filename = filedialog.askopenfilename(initialdir = "/",
										title = "Select a File",
										filetypes = (("Text files",
														"*.txt*"),
													("all files",
														"*.*")))
	
	
	return (""+filename)
	
def getEmail():
	
    return input("Please enter your email address:")




