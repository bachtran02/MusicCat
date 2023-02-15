# REQUIRED: WINDOWS - pip, python, java

DIR=.venv/
if [ -d "$DIR" ];
then
    echo "$DIR directory exists."
    source .venv/Scripts/activate
else
	echo "$DIR directory does not exist."
    echo "Creating venv..."

    if python -c 'import pkgutil; exit(not pkgutil.find_loader("venv"))'; 
    then
        echo 'venv found'
    else
        echo 'venv not found'
        echo "install venv package"
        python -m pip install --user virtualenv

    fi

    python -m venv .venv
    source .venv/Scripts/activate
    pip install -r requirements.txt

fi

cd lavalink_server && java -jar Lavalink.jar & sleep 8 && python -O -m bot