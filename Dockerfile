FROM python:3.8

WORKDIR /code

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt
ADD "20220523165127_E8A2B3" /code/20220523165127_E8A2B3
RUN pip install "./20220523165127_E8A2B3"

COPY . .

CMD ["python", "-u", "app.py"]