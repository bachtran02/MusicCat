FROM python:3.10
RUN apt-get update

# COPY bot/ bot/
# COPY requirements.txt requirements.txt
# COPY .env .env

WORKDIR /MusicCat
COPY . /MusicCat

RUN pip install -r requirements.txt
CMD ["python", "-O", "-m", "bot" ]