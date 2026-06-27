# Use an official lightweight Python image.
FROM python:3.10-slim

# Prevent Python from writing pyc files to disk (optional).
ENV PYTHONDONTWRITEBYTECODE 1

# Prevent Python from buffering stdout and stderr (optional).
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container to /code.
WORKDIR /code

RUN mkdir -p /code/static /code/media

# Install pip requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application's code into the container
COPY . .

# Collect static files
RUN python manage.py collectstatic --no-input && ls /code/static

# Specify the port number the container should expose
EXPOSE 8000

# Command to run the application using Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "library_demo_project.wsgi:application"]
