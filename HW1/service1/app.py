import psycopg2
import boto3
from flask import Flask, flash, render_template, request, redirect, url_for 
from werkzeug.utils import secure_filename
from botocore.exceptions import NoCredentialsError
from urllib.parse import quote
import re



app = Flask(__name__)


@app.route('/')
def hello_world():
    return 'Hello World'


@app.route('/requestService', methods = ['POST'])
def requestService():
    photo = request.get_json()['img']
    email = request.get_json()['email']
    emailIsValid = handleEmail(email)
    imageURL = handleImage(photo)
    if emailIsValid:
        return 0
    return 'Hello World'


@app.route('/trackRequest')
def trackRequest():
    return 'Hello World'


@app.route('/createDatabase')
def createDatabase():
    conn = psycopg2.connect(
        host="cchw1-9931097",
        database="cchw1-9931097",
        user="root",
        password="nRocULwUkiK3sVS3QedxqYKw")

    cur = conn.cursor()
    cur.execute("""DROP TABLE IF EXISTS requests;""")
    cur.execute("""
                CREATE TABLE requests (id SERIAL PRIMARY KEY,
                            email varchar (150) NOT NULL,
                            status varchar (50) NOT NULL,
                            oldImageURL varchar (300),
                            imageCaption varchar (200),
                            newImageURL varchar (300),
                            date_added date DEFAULT CURRENT_TIMESTAMP);
                            """)

    
    data = cur.fetchall() 
    cur.close() 
    conn.close() 
  
    return render_template('index.html', data=data) 

def insertIntoDatabase(email,imageURL):
    status = "pending"

    conn = psycopg2.connect(
        host="cchw1-9931097",
        database="cchw1-9931097",
        user="root",
        password="nRocULwUkiK3sVS3QedxqYKw")

    cur = conn.cursor()
    cur.execute("""INSERT INTO requests (email, status,oldImageURL)
            VALUES (%s, %s)
            RETURNING *;""",
            (
            email,
            status,
            imageURL
            )
        )
    

     # Fetch the data 
    data = cur.fetchall() 
  
    # close the cursor and connection 
    cur.close() 
    conn.close() 
  
    return render_template('index.html', data=data) 

def handleEmail(email):

# Click on Edit and place your email ID to validate
    valid = re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email)
    return valid

def handleImage(file):

    imageURL = sendToObjectStorage(file)
    return imageURL 

def sendToObjectStorage(file):

    LIARA_ENDPOINT = "storage.c2.liara.space"
    LIARA_ACCESS_KEY = "aaq6bq7e4u9ercei"
    LIARA_SECRET_KEY = "81c9bf56-4dd8-4698-9cd8-a6248b6300fa"
    LIARA_BUCKET_NAME = "cchw1-9931097"

    s3 = boto3.client(
        "s3",
        endpoint_url=LIARA_ENDPOINT,
        aws_access_key_id=LIARA_ACCESS_KEY,
        aws_secret_access_key=LIARA_SECRET_KEY,
        
)
    s3.upload_fileobj(file, LIARA_BUCKET_NAME, file.filename)
    filename_encoded = quote(file.filename)
    permanent_url = f"https://{LIARA_BUCKET_NAME}.{LIARA_ENDPOINT.replace('https://', '')}/{filename_encoded}"
    return permanent_url




# main driver function
if __name__ == '_apt install python3.10-venv_main__':

    app.run()
