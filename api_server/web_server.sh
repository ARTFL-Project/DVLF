#!/bin/sh

# Define the number of workers for your app. Between 4 and 12 should be fine.
WORKERS=8

# Define on which port the webserver will be listening. If you have a webserver already listening to port 80
# you should proxy requests to below port to the app
PORT=443

# If using an https connection (you should), define your SSL keys and certificate locations here
KEYFILE=/etc/letsencrypt/live/mirabeau.lib.uchicago.edu/privkey.pem
CERTFILE=/etc/letsencrypt/live/mirabeau.lib.uchicago.edu/fullchain.pem

if [ -z "$KEYFILE" ]
then
    gunicorn -k uvicorn.workers.UvicornWorker -b :$PORT -w 4 --access-logfile=/DVLF/api_server/access.log --error-logfile=/DVLF/api_server/error.log --chdir /DVLF web_app:app
else
    gunicorn --keyfile=$KEYFILE --certfile=$CERTFILE -k uvicorn.workers.UvicornWorker -b :$PORT -w 4 --access-logfile=/DVLF/api_server/access.log --error-logfile=/DVLF/api_server/error.log --chdir /DVLF web_app:app
fi