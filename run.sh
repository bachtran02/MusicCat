#!/bin/bash

sudo apt install python3.10-venv

FILE=LavalinkServer/Lavalink.jar
if [[ -f "$FILE" ]];
then 
    echo "$FILE file exists."
else
    echo "$FILE file doesn't exist"
    echo "installing latest version of Lavalink.jar..."
    cd LavalinkServer
    curl -L https://github.com/freyacodes/Lavalink/releases/latest/download/Lavalink.jar > Lavalink.jar
    cd ../
fi

DIR=.venv/
if [ -d "$DIR" ];
then
    echo "$DIR directory exists."
    source .venv/bin/activate
else
	echo "$DIR directory does not exist."
    echo "Creating venv..."

    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt

fi

cd LavalinkServer && java -jar Lavalink.jar & sleep 8 && python3 -O -m bot