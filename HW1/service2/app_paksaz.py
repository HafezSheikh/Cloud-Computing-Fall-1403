import json
import boto3
import pika
import psycopg2
from PIL import Image
from transformers import AutoProcessor, BlipForConditionalGeneration
from flask import Flask, jsonify
from io import BytesIO
from urllib.parse import urlparse

app = Flask(__name__)

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
#RabbitMQ
RABBITMQ_URL = 'amqps://enukjhfn:DB4_Sm1TxUXlYKui7UvYflILYpROtmlJ@hummingbird.rmq.cloudamqp.com/enukjhfn'
rabbitmq_params = pika.URLParameters(RABBITMQ_URL)


#PostgreSQL
conn = psycopg2.connect(
    host="cchw1-9931097",
    database="cchw1-9931097",
    user="root",
    password="nRocULwUkiK3sVS3QedxqYKw")

cur = conn.cursor()

processor = AutoProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")

def extract_s3_key(url):
    parsed_url = urlparse(url)
    s3_key = parsed_url.path.lstrip('/')  
    return s3_key

def generate_caption(s3_key):
    try:
        url = s3_key.replace("https://storage.c2.liara.space/cchw1-9931097/", "")
        response = s3.get_object(Bucket=LIARA_BUCKET_NAME, Key=url)
        image_data = response['Body'].read()

        image = Image.open(BytesIO(image_data))

        text = "A picture of"
        #
        inputs = processor(images=image, text=text, return_tensors="pt")

        #
        outputs = model.generate(**inputs)
        caption = processor.decode(outputs[0], skip_special_tokens=True)
        return caption

    except Exception as e:
        print(f"Error generating caption: {e}")
        return None

def update_image_caption(image_id, caption):
    try:
        # 
        cur.execute("""
            UPDATE requests 
            SET imagecaption = %s, status = 'ready' 
            WHERE id = %s;
        """, (caption, image_id))
        conn.commit()
        print(f"Image {image_id} updated successfully with caption: {caption}")

    except Exception as e:
        conn.rollback()
        print(f"Error updating image {image_id}: {e}")

def process_message(ch, method, properties, body):
    try:
        # پردازش پیام دریافتی از RabbitMQ
        message = json.loads(body)
        image_id = message['image_id']

        # خواندن URL عکس از دیتابیس
        cur.execute("SELECT newimageurl FROM reequests WHERE id = %s;", (image_id,))
        result = cur.fetchone()
        if result:
            image_url = result[0]
            print(image_url)
            # تولید کپشن برای عکس
            caption = generate_caption(image_url)
            if caption:
                # آپدیت کپشن در دیتابیس و تغییر وضعیت
                update_image_caption(image_id, caption)

    except Exception as e:
        print(f"Error processing message: {e}")

@app.route('/status/<int:image_id>', methods=['GET'])
def get_image_status(image_id):
    try:
        cur.execute("SELECT status, imagecaption FROM requests WHERE id = %s;", (image_id,))
        result = cur.fetchone()
        if result:
            status, caption = result
            return jsonify({'image_id': image_id, 'status': status, 'caption': caption}), 200
        else:
            return jsonify({'error': 'Image not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def start_consumer():
    # اتصال به RabbitMQ
    connection = pika.BlockingConnection(rabbitmq_params)
    channel = connection.channel()

    # اطمینان از وجود صف
    channel.queue_declare(queue='image_processing')

    # تنظیم listener برای دریافت پیام‌ها
    channel.basic_consume(
        queue='image_processing',
        on_message_callback=process_message,
        auto_ack=True
    )

    print('Waiting for messages. To exit press CTRL+C')

    # شروع حلقه برای گوش دادن به صف
    channel.start_consuming()

if __name__ == '__main__':
    # Start the consumer in a separate thread so the Flask app can run in parallel
    from threading import Thread
    consumer_thread = Thread(target=start_consumer)
    consumer_thread.start()

    # Run the Flask app
    app.run()