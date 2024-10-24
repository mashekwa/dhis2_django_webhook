import logging
import json
from confluent_kafka import Consumer, KafkaException
from tasks import process_lab_results, send_telegram_message
from decouple import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


KAFKA_CONFIG = {
    "bootstrap.servers": config("KAFKA_BOOTSTRAP_SERVERS"),
    "security.protocol": config("KAFKA_SECURITY_PROTOCOL"),
    "sasl.mechanism": config("KAFKA_SASL_MECHANISM"),
    "sasl.username": config("KAFKA_USERNAME"),
    "sasl.password": config("KAFKA_PASSWORD"),
    "group.id": config("KAFKA_GROUP_ID"),
    'socket.timeout.ms': 30000,  # Increase to 30 seconds
    'message.timeout.ms': 30000,  # Increase to 30 seconds
    'retries': 5,  # Retry sending the message
    'debug': 'all',
    'client.id': 'znphi-producer',
    'acks': 'all',  # Ensure all replicas acknowledge
}

tele_id = config("TELEGRAM_CHAT_ID")

# Other Kafka Configuration
KAFKA_TOPIC = config("KAFKA_TOPIC")
GROUP_ID = config("GROUP_ID")

def kafka_consumer():

    consumer = Consumer(KAFKA_CONFIG )

    try:
        consumer.subscribe([KAFKA_TOPIC])
        logger.info(f"Listening for messages on topic: {KAFKA_TOPIC}")

        while True:
            message = consumer.poll(timeout=1.0)

            if message is None:
                logger.info(f"**---NO MSG---**")
                continue  # No new messages
            if message.error():
                raise KafkaException(message.error())

            try:
                data = json.loads(message.value().decode('utf-8'))
                logger.info(f"**---RECEIVED MSG---**: \n{data}")
                msg =f'DISA LAB RESULTS RECEIVED: \n{data}'
                send_telegram_message.delay(tele_id, msg)
                process_lab_results.delay(data)  # Trigger Celery task

            except Exception as e:
                logger.error(f"Failed to process message: {e}")

    except Exception as e:
        logger.error(f"Kafka consumer error: {e}")
    finally:
        consumer.close()

if __name__ == "__main__":
    kafka_consumer()
