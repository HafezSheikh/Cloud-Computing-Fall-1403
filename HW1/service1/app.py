import io               
import base64                           
from PIL import Image
import psycopg2
import boto3
from flask import Flask, render_template, request, jsonify, abort
import re
import pika
import os
import json

app = Flask(__name__)

@app.route('/requestService', methods = ['POST'])
def requestService():
    if not request.json or 'img' not in request.json: 
        abort(400)
    image = request.get_json()['img']
    email = request.get_json()['email']
    emailIsValid = handleEmail(email)
    import time
    timestr = time.strftime("%Y%m%d-%H%M%S")    
    filename = timestr
    imageURL = handleImage(image,filename )
    if emailIsValid:
        id = insertIntoDatabase(email,imageURL)
        if(id):
            insertIntoRabbitMQ(id)
            return (id) 

    return 'invalid request'


@app.route('/status/<int:image_id>', methods=['GET'])
def get_image_status(image_id):
    conn = psycopg2.connect(
        host = os.environ.get('DB_HOST'),
        database = os.environ.get('DB_DATABASE'),
        user = os.environ.get('DB_USER'),
        password = os.environ.get('DB_KEY'))

    cur = conn.cursor()
    try:
        cur.execute("SELECT status, imagecaption FROM requests WHERE id = %s;", (image_id,))
        conn.commit()
        result = cur.fetchone()
        if result:
            status, caption = result
            return jsonify({'image_id': image_id, 'status': status, 'caption': caption}), 200
        else:
            return jsonify({'error': 'Image not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/createDatabase')
def createDatabase():
    conn = psycopg2.connect(

        host = os.environ.get('DB_HOST'),
        database = os.environ.get('DB_DATABASE'),
        user = os.environ.get('DB_USER'),
        password = os.environ.get('DB_KEY')
        )

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
        host = os.environ.get('DB_HOST'),
        database = os.environ.get('DB_DATABASE'),
        user = os.environ.get('DB_USER'),
        password = os.environ.get('DB_KEY'))

    cur = conn.cursor()
    cur.execute("""INSERT INTO requests (email, status, oldimageurl)
        VALUES (%s, %s, %s)
        RETURNING id;""",
            (
            email,
            status,
            imageURL
            )
        )
    
    conn.commit()
     # Fetch the data 
    result = cur.fetchall() 
    if result:
            id = result
            cur.close() 
            conn.close() 
            x = {"image_id":id}
            s1 = json.dumps(x)


            return s1
    else:
        return jsonify({'error': 'Image not found'}), 404
    # close the cursor and connection 

  

def handleEmail(email):

# Click on Edit and place your email ID to validate
    valid = re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email)
    return valid

def handleImage(file,filename):

    # convert it into bytes  
    LIARA_ENDPOINT = os.environ.get('LIARA_ENDPOINT')
    LIARA_ACCESS_KEY = os.environ.get('LIARA_ACCESS_KEY')
    LIARA_SECRET_KEY = os.environ.get('LIARA_SECRET_KEY')
    LIARA_BUCKET_NAME = os.environ.get('LIARA_BUCKET_NAME')


    s3 = boto3.client(
        "s3",
        endpoint_url=LIARA_ENDPOINT,
        aws_access_key_id=LIARA_ACCESS_KEY,
        aws_secret_access_key=LIARA_SECRET_KEY,
        
)   
    img_bytes = base64.b64decode(file.encode('utf-8'))
    s3.upload_fileobj(io.BytesIO(img_bytes),LIARA_BUCKET_NAME,filename)
    # s3.upload_fileobj(file, LIARA_BUCKET_NAME, filename)
    permanent_url = f"https://{LIARA_BUCKET_NAME}.{LIARA_ENDPOINT.replace('https://', '')}/{filename}"
    return permanent_url
 
def insertIntoRabbitMQ(jsonObj):
    url = os.environ.get('CLOUDAMQP_URL')
    params = pika.URLParameters(url)
    connection = pika.BlockingConnection(params)
    channel = connection.channel() # start a channel
    # channel.queue_declare(queue='image_processing') # Declare a queue
    channel.basic_publish(exchange='',
                      routing_key='image_processing',
                      body=jsonObj)
    return "done"





if __name__ == '_apt install python3.10-venv_main__':
    app.run()