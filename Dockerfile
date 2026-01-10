# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application's code to the working directory
# Note: We copy the 'app' directory into a subdirectory of the same name inside the container
COPY ./app /app/app

# Set the PYTHONPATH to the working directory to ensure module resolution
ENV PYTHONPATH=.

# Expose the port the app runs on
EXPOSE 8000

# Run the command to start the server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
