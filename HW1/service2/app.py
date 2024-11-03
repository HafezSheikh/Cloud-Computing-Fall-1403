import psycopg2

import json
import boto3
import pika
import psycopg2
from PIL import Image
from flask import Flask, jsonify
from io import BytesIO
import requests
import os
import logging
from threading import Thread
import urllib

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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

# RabbitMQ
url = 'amqps://enukjhfn:DB4_Sm1TxUXlYKui7UvYflILYpROtmlJ@hummingbird.rmq.cloudamqp.com/enukjhfn'
rabbitmq_params = pika.URLParameters(url)

# PostgreSQL

conn = psycopg2.connect(
    host = os.environ.get('DB_HOST'),
    database = os.environ.get('DB_DATABASE'),
    user = os.environ.get('DB_USER'),
    port = '34870',
    password = os.environ.get('DB_KEY'))

cur = conn.cursor()


def generate_caption(url):
    try:
        with urllib.request.urlopen(url) as ur:
            image = ur.read()


        API_URL = "https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-base"
        headers = {"Authorization": "Bearer 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"}

        response = requests.post(API_URL, headers=headers, data=image)
        logging.info("Caption generated successfully.")
        return response.json()

    except Exception as e:
        logging.error(f"Error generating caption: {e}")
        return None


def update_image_caption(image_id, caption):
    try:
        
        cur.execute("""
            UPDATE requests 
            SET imagecaption = %s, status = 'ready' 
            WHERE id = %s;
        """, (caption, image_id))
        conn.commit()
        logging.info(f"Image {image_id} updated successfully with caption: {caption}")

    except Exception as e:
        conn.rollback()
        logging.error(f"Error updating image {image_id}: {e}")


def process_message(ch, method, properties, body):
    try:
        message = json.loads(body)
        image_id = message['image_id'][0]
        
        logging.info(f"Processing image ID: {image_id}")

        cur.execute("SELECT oldimageurl FROM requests WHERE id = %s;", (image_id))
        result = cur.fetchone()

        if result:
            image_url = result[0]
            logging.info(f"Image URL fetched: {image_url}")
            caption = generate_caption(image_url)
            if caption:
                cap = caption[0].get('generated_text')
                update_image_caption(image_id[0], cap)
        else:
            logging.warning(f"No image found for ID: {image_id}")

    except Exception as e:
        logging.error(f"Error processing message: {e}")


def start_consumer():
    logging.info("Starting RabbitMQ consumer thread...")
    connection = pika.BlockingConnection(rabbitmq_params)
    channel = connection.channel()

    channel.basic_consume(
        queue='image_processing',
        on_message_callback=process_message,
        auto_ack=True
    )

    logging.info("RabbitMQ consumer is now listening for messages...")
    channel.start_consuming()



# Start the consumer in a separate thread
consumer_thread = Thread(target=start_consumer)
consumer_thread.start()

logging.info("Consumer thread has started.")

    # Run the Flask app
app.run()
