To use sherpa api
 a) Note that a description of the SHERPA system is in the subdirectory sherpa/docs/SHERPA.docxs
 b) make sure your python installation is python 3. The scripts can be run as executables provided their permissions support this, and that your (unix) environment calls up python3 when the command
     % /usr/bin/env python3
 is executed.   Alternatively, you can call the scripts as arguments to the application python3

 c) make sure that your $PYTHONPATH includes the path to the directory in which this README.txt appears,
    'sherpa'

 ## Run the Flask Server

Set up a [virtual environment](https://docs.python-guide.org/dev/virtualenvs/) for the backend server and activate it.

Switch directory to the "server" folder and use pip to install the required files.

```bash
cd server
pip install -r requirements.txt 
```

Run the flask app to start up the server.

```bash
export FLASK_APP=api.py
export FLASK_ENV=development # remove this line when deploying and not debugging
flask run
```

## Run the React UI

Start up the node server to load the react application.

### Contact
Questions can be passed to the SHERPA developer at dmnicol@illinois.edu
Questions regarding the SHERPA API can be passed to cwwong3@illinois.edu



