
from tkinter import filedialog
import requests
import base64
# Function for opening the 
# file explorer window

api_url = "https://cchw1-9931097-s1.liara.run/requestService"


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


# main driver function
if __name__ == '__main__':
	filename = browseFiles()
	email = getEmail()

	with open(filename, "rb") as img: 
		string = img.read()

	response = requests.post(url= api_url, json={'img':string})
	print(response.content)
	