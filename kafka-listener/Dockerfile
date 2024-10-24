# Use official Python image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR /app

# Copy the necessary files into the container
COPY . .
COPY .env /app/.env

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install python-decouple

# Entry point for the Kafka listener script
CMD ["python", "kafka_listener.py"]

