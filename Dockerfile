# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONUNBUFFERED 1
ENV FLASK_APP=app.py
# Default port, can be overridden at runtime if needed
ENV PORT=8888
# Default host, ensures Flask listens on all interfaces
ENV FLASK_RUN_HOST=0.0.0.0

# Set the working directory in the container
WORKDIR /app

# Install system dependencies that might be needed (unlikely for this app, but good practice)
# RUN apt-get update && apt-get install -y --no-install-recommends some-package && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Make port 8888 available to the world outside this container
EXPOSE 8888

# Define environment variable for the Azure SAS URL (pass this during 'docker run')
# We don't set a default here to force the user to provide it.
# ENV AZURE_CONTAINER_SAS_URL="value_passed_at_runtime"

# Run app.py when the container launches using Gunicorn
# Use Gunicorn for production runs - more robust than Flask's dev server
# Bind to 0.0.0.0 to accept connections from outside the container
# Use gevent worker for better async handling if needed, but default sync is fine for this.
# Number of workers (adjust based on your server's CPU cores, e.g., 2*cores + 1)
CMD ["gunicorn", "--bind", "0.0.0.0:8888", "--workers", "4", "app:app"]

# --- Alternatively, for development/testing using Flask's built-in server ---
# CMD ["flask", "run"]
# Note: If using `flask run`, ensure FLASK_HOST and FLASK_PORT are correctly set.
# Gunicorn is preferred for stability.
