# Use the official Python base image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements.txt file into the container
COPY app/requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code into the container
COPY app .

# Expose the port the app runs on
EXPOSE 8080

# Command to run the application
CMD ["python", "main.py"]
