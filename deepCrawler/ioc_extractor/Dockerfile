FROM python:3

WORKDIR /usr/src/ioc_extractor

COPY requirements.txt ./

RUN pip3 install --no-cache-dir -r requirements.txt

COPY extractor.py .

ENV PYTHONUNBUFFERED=1

CMD [ "python", "extractor.py"]
