The Brighton and Hove Python User Group Website
===============================================

A very simple database-free website using the [Flask microframework](http://flask.pocoo.org).

You can see it running at [http://brightonpy.org](http://brightonpy.org)

How to install and run locally
------------------------------

(Assumes you have Pip, virtualenv and virtualenvwrapper installed).

    git clone git@github.com:j4mie/brightonpy.org.git
    cd brightonpy.org
    mkvirtualenv brightonpy
    pip install -E brightonpy -r requirements.txt
    python brighton.py

The development server should now be running on [localhost:5000](http://localhost:5000)

