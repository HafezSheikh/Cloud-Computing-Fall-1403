
from tkinter import filedialog
import requests
import base64
import json    
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
	# filename = browseFiles()
	filename = "/home/hafez/Desktop/images.jpeg"
	# email = getEmail()
	email = "hafezsheikh@gmail.com"
	with open(filename, "rb") as f:
		im_bytes = f.read()        
	im_b64 = base64.b64encode(im_bytes).decode("utf8")
	payload = json.dumps({"img": im_b64, "email": email})
	headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
	response = requests.post(url= api_url, data=payload, headers=headers)
	print(response.content)
	