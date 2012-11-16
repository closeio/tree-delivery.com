Setup
-----
1. `git submodule update --init --recursive`
1. `virtualenv-2.7 --distribute venv`
1. `. venv/bin/activate`
1. `pip install -r requirements.txt`

Run
------
1. `python app.py`

Deploy
------
1. `git remote add heroku git@heroku.com:tree-delivery.git`
2. `git push heroku master`

