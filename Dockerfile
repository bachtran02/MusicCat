FROM python:3.10
RUN apt-get update && apt-get install -y git

COPY bot/ bot/
COPY requirements.txt requirements.txt
COPY .env .env

RUN pip install -r requirements.txt
CMD ["python", "-O", "-m", "bot" ]