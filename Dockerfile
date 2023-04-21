#   Use an official python runtime
FROM python:3.8-slim-buster

#   Set the working directory
WORKDIR /app

#   Copy the codebase in the current directory to the container /app
COPY . /app

#   Upgrade pip
RUN pip install --upgrade pip

#   Install needed packages
RUN pip install -r requirements.txt

#   Set the default command to run when starting the container
CMD ["python", "app.py"]