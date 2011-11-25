#!/bin/bash

packages=( Flask Flask-SQLAlchemy Flask-WTF Flask-Uploads Flask-Mail 
            Flask-Assets BeautifulSoup PIL pytz markdown tweepy 
            bitlyapi whoosh )

for package in ${packages[@]}
do
    echo "========================================================"
    echo "Installing: $package"
    pip install $package
    echo "========================================================"
done
