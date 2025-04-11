# Use the official Python image as a base
FROM python:3.13

# Set the working directory
WORKDIR /app

# Copy the project files to the container
COPY . /app

# Install setuptools (to fix distutils issues) and dependencies
RUN pip install --upgrade pip setuptools && pip install --no-cache-dir -r requirements.txt

# Expose the port Flask runs on
EXPOSE 5000

# Run the application
CMD ["python", "main.py"]
