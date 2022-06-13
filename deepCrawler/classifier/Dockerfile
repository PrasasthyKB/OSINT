# As Scrapy runs on Python, I choose the official Python 3 Docker image.
FROM python:3

# Set the working directory to /usr/src/app.
WORKDIR /usr/src/classifier

# Copy the file from the local host to the filesystem of the container at the working directory.
COPY requirements.txt ./

# Install dependecies specified in requirements.txt.
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy the project source code from the local host to the filesystem of the container at the working directory.
COPY IoCClassifier.py .
RUN mkdir model_checkpoints
#COPY ./model_checkpoints ./model_checkpoints

ENV PYTHONUNBUFFERED=1
CMD [ "python", "-u", "IoCClassifier.py"]
