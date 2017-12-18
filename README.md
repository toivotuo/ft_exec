# ft_exec

## Welcome
That project is just implementation double entry mechanism and
API for several operations.

## Setup
1. Create new virtualenv (python 2.7)
2. `cd ft_exec & pip install requirements.txt`
3. Run standard commands
`python manage.py migrate` and `python manage.py createsuperuser`
4. Load initial data in DB
`python manage.py loaddata issuer/fixtures/initial_data.json`
5. Run django app
` python manage.py runserver`
6. Open http://127.0.0.1:8000/v1.0/schema/ in your browser


## Django's model scheme
![Alt text](model_scheme.png?raw=true "Model Scheme")

## manage.py commands
1. `python manage.py load_money <cardholder> <amount> <currency>` - load money to account
2. `python manage.py clearing` - emulate 'scheme clearing' mechanism

## TODO
1. API endpoint for transactions
2. unit tests
3. full documentation
4. run via Docker
5. something else