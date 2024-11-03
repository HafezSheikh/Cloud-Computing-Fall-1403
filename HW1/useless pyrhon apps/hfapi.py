import os
import psycopg2
import boto3
import requests
from flask import Flask
from mailersend import emails
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

LIARA_ENDPOINT = 'https://storage.c2.liara.space'
LIARA_ACCESS_KEY = 'fp48sh94qqsknsfe'
LIARA_SECRET_KEY = '81ebeed5-3412-4ff5-a40b-b9d6fa0cfc07'
LIARA_BUCKET_NAME = 'cchw1-9931097-os'



HF_API_URL = "https://api-inference.huggingface.co/models/ZB-Tech/Text-to-Image"
headers = {"Authorization": "Bearer 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"}


s3 = boto3.client(
    "s3",
    endpoint_url=LIARA_ENDPOINT,
    aws_access_key_id=LIARA_ACCESS_KEY,
    aws_secret_access_key=LIARA_SECRET_KEY,
        
)   

def generate_image_from_caption(caption):
    response = requests.post(HF_API_URL, headers=headers, json={"inputs": caption})
    if response.status_code == 200:
        return response.content
    else:
        raise Exception(f"Failed to generate image. Status code: {response.status_code}, {response.text}")


def process_rows():
    try:
        conn = psycopg2.connect(
            host = 'kazbek.liara.cloud',
    		database = 'cchw1-9931097',
    		user = 'root',
    		port = '34870',
    		password = 'Z270PMuaUXPILMPhlnVDkScY')

        cur = conn.cursor()
     
        cur.execute("SELECT id, imagecaption FROM requests WHERE status = 'ready'")
        rows = cur.fetchall()

        for row in rows:
            row_id, caption = row
            try:
                image_bytes = generate_image_from_caption(caption)

                s3_key = f"{row_id}.png"
                s3.put_object(Bucket=LIARA_BUCKET_NAME, Key=s3_key, Body=image_bytes)

                download_url = f"{LIARA_ENDPOINT}/{LIARA_BUCKET_NAME}/{s3_key}"

                cur.execute("UPDATE requests SET newimageurl = %s, status = 'done' WHERE id = %s", 
                               (download_url, row_id))
                sendMail(row_id)
                conn.commit()

            except Exception as e:

                print(f"Error processing row {row_id}: {e}")
                cur.execute("UPDATE requests SET status = 'failure' WHERE id = %s", 
                               (row_id,))
                conn.commit()

        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error connecting to the database: {e}")


scheduler = BackgroundScheduler()
scheduler.add_job(func=process_rows, trigger="interval", seconds=5)
scheduler.start()

def sendMail(id):
    conn = psycopg2.connect(
        host = 'kazbek.liara.cloud',
    	database = 'cchw1-9931097',
    	user = 'root',
    	port = '34870',
    	password = 'Z270PMuaUXPILMPhlnVDkScY')

    cur = conn.cursor()
    
    cur.execute("SELECT email, newimageurl FROM requests WHERE id = %s;", (id,))
    conn.commit()
    result = cur.fetchone()
    if not result:
        return "error"
    email = result[0]
    image_url = result[1]
    
    api_key = "mlsn.b73ed64171213750a2d55b6a5879afab1302edd5fb6e84e463df6ba56f79fc15"
    mailer = emails.NewEmail(api_key)
    mail_body = {}
    mail_from = {
    "name": "hafez",
    "email": "MS_796KQd@trial-zr6ke4npndygon12.mlsender.net",
    }

    recipients = [
        {
        "name":"",
        "email": email,
        }
    ]
    mailer.set_mail_from(mail_from, mail_body)
    mailer.set_mail_to(recipients, mail_body)
    mailer.set_plaintext_content(image_url, mail_body)
    mailer.set_subject("Your Requested Image", mail_body)


# using print() will also return status code and data
    mailer.send(mail_body)



@app.route('/')
def index():
    return "Flask Service is Running"


if __name__ == '__main__':
    try:
        app.run()
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        


