FROM python:3.10

COPY bot/ bot/
COPY requirements.txt requirements.txt
COPY .env .env

RUN pip install -r requirements.txt
CMD ["python", "-O", "-m", "bot" ]