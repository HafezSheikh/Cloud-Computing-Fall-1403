import io               
import base64                           
from PIL import Image
import psycopg2
import boto3
from flask import Flask, render_template, request, jsonify, abort
import re



app = Flask(__name__)


@app.route('/')
def hello_world():
    return 'Hello World'


@app.route('/requestService', methods = ['POST'])
def requestService():
    if not request.json or 'img' not in request.json: 
        abort(400)
    image = request.get_json()['img']
    email = request.get_json()['email']
    emailIsValid = handleEmail(email)
    filename = email + ".jpeg"
    imageURL = handleImage(image,filename )
    if emailIsValid:
        return insertIntoDatabase(email,imageURL)
    return 'invalid request'


@app.route('/trackRequest')
def trackRequest():
    conn = psycopg2.connect(
        host="cchw1-9931097",
        database="cchw1-9931097",
        user="root",
        password="nRocULwUkiK3sVS3QedxqYKw")

    cur = conn.cursor()
    cur.execute("""SELECT status FROM requests WHERE(id = %s)""",
            (id)
        )
    

    conn.commit()
     # Fetch the data 
    data = cur.fetchall() 
  
    # close the cursor and connection 
    cur.close() 
    conn.close() 
  
    return data 


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
                            oldimageurl varchar (300),
                            imagecaption varchar (200),
                            newimageurl varchar (300),
                            date_added date DEFAULT CURRENT_TIMESTAMP);
                            """)
    cur.execute("""INSERT INTO requests (email, status, oldimageurl)
        VALUES (%s, %s, %s)
        RETURNING *;""",
            (
            "dummy@dummy.com",
            "dummy Status",
            "dummyURL"
            )
        )

    conn.commit()

    data = cur.fetchall() 
    cur.close() 
    conn.close() 
  
    return data

def insertIntoDatabase(email,imageURL):
    status = "pending"

    conn = psycopg2.connect(
        host="cchw1-9931097",
        database="cchw1-9931097",
        user="root",
        password="nRocULwUkiK3sVS3QedxqYKw")

    cur = conn.cursor()
    cur.execute("""INSERT INTO requests (email, status, oldimageurl)
        VALUES (%s, %s, %s)
        RETURNING *;""",
            (
            email,
            status,
            imageURL
            )
        )
    
    conn.commit()
     # Fetch the data 
    data = cur.fetchall() 
  
    # close the cursor and connection 
    cur.close() 
    conn.close() 
  
    return data

def handleEmail(email):

# Click on Edit and place your email ID to validate
    valid = re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email)
    return valid

def handleImage(file,filename):

    # convert it into bytes  
    photo = base64.b64decode(file.encode('utf-8'))

    LIARA_ENDPOINT = "https://storage.c2.liara.space"
    LIARA_ACCESS_KEY = "aaq6bq7e4u9ercei"
    LIARA_SECRET_KEY = "81c9bf56-4dd8-4698-9cd8-a6248b6300fa"
    LIARA_BUCKET_NAME = "cchw1-9931097"

    s3 = boto3.client(
        "s3",
        endpoint_url=LIARA_ENDPOINT,
        aws_access_key_id=LIARA_ACCESS_KEY,
        aws_secret_access_key=LIARA_SECRET_KEY,
        
)   
    s3.upload_fileobj(io.BytesIO(photo),LIARA_BUCKET_NAME,filename)
    # s3.upload_fileobj(file, LIARA_BUCKET_NAME, filename)
    permanent_url = f"https://{LIARA_BUCKET_NAME}.{LIARA_ENDPOINT.replace('https://', '')}/{filename}"
    return permanent_url
 



if __name__ == '_apt install python3.10-venv_main__':
    app.run()
