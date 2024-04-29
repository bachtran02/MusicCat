FROM python:3.10
RUN apt-get update

WORKDIR /MusicCat
COPY . /MusicCat

RUN pip install -r requirements.txt
CMD ["python", "-O", "-m", "bot" ]