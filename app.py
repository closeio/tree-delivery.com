import os, json
from flask import Flask, render_template, request, redirect
from flask.exceptions import BadRequest
from flask.ext.mail import Mail, Message
from flask_heroku import Heroku
import stripe
from urlparse import urlparse, urlunparse

# hardcoded are the Test keys
# to set the Live keys for production, we do:
# https://devcenter.heroku.com/articles/config-vars#setting-up-config-vars-for-a-deployed-application
stripe_keys = {
    'secret_key': os.environ.get('STRIPE_SECRET_KEY', 'YzJ79QCHT7GSyr1eXdBqe0roReJZNb9B'),
    'publishable_key': os.environ.get('STRIPE_PUBLISHABLE_KEY', 'pk_ggtxMwrQDJz6gWeYyybNFoCaN2Dad')
}

stripe.api_key = stripe_keys['secret_key']

app = Flask(__name__)
heroku = Heroku(app)

# Flask-Mail - http://packages.python.org/Flask-Mail/
app.config['MAIL_FAIL_SILENTLY'] = False
app.config['MAIL_SERVER'] = app.config['SMTP_SERVER']
app.config['MAIL_USERNAME'] = app.config['SMTP_LOGIN']
app.config['MAIL_PASSWORD'] = app.config['SMTP_PASSWORD']
mail = Mail(app)

SENDER = 'info@tree-delivery.mailgun.org'
RECIPIENTS = ['engineering@elasticsales.com']

# in cents
PRICES = {
    'tree_small': 12500,
    'tree_medium': 17500,
    'tree_large': 25000,
    'skirt1': 2000,
    'skirt2': 5000,
    'skirt3': 8000,
}

"""
ADMINS = ['phil@elasticsales.com']
if not app.debug:
    import logging
    from logging.handlers import SMTPHandler
    mail_handler = SMTPHandler('127.0.0.1', 'error@tree-delivery.com', ADMINS, '[Tree-Delivery.com] ERROR')
    mail_handler.setLevel(logging.ERROR)
    app.logger.addHandler(mail_handler)
"""

@app.before_request
def redirect_to_www_ssl():
    """Redirect non-www and non-ssl requests to www+ssl."""
    if app.debug:
        return
    urlparts = urlparse(request.url)
    if not (request.is_secure or request.headers.get('X-Forwarded-Proto', 'http') == 'https') or urlparts.netloc != 'www.tree-delivery.com':
        urlparts_list = list(urlparts)
        urlparts_list[0] = 'https'
        urlparts_list[1] = 'www.tree-delivery.com'
        return redirect(urlunparse(urlparts_list), code=301)

@app.route('/')
def index():
    return render_template('index.html', stripe_publishable_key=stripe_keys['publishable_key'], prices=json.dumps(PRICES))


@app.route('/charge', methods=['POST'])
def charge():

    email = request.form['email']
    phone = request.form['phone']
    address = request.form['address']
    city = request.form['city']
    state = request.form['state']
    zipcode = request.form['zip']
    user_amount = int(request.form['amount'])

    tree_type = request.form['tree_type']
    skirt_type = request.form.get('skirt_type', None)

    amount = 0
    amount += PRICES[tree_type]
    if skirt_type:
        amount += PRICES[skirt_type]

    if user_amount != amount:
        return BadRequest('Invalid amount. Please get in touch with us if you think this is a mistake.')

    # skirt1 - http://www.amazon.com/Imperial-MW1029-Christmas-Skirt-Green/dp/B005YFYSZE/
    # skirt2 - http://www.amazon.com/Snowman-Christmas-Accented-Snowflakes-Adorable/dp/B003WWHIAI/
    # skirt3 - http://www.amazon.com/Kurt-Adler-50-Inch-Christmas-Treeskirt/dp/B007KKW0RE/

    msg = Message("[Tree-Delivery.com] New Order", sender=SENDER, recipients=RECIPIENTS)
    msg.body = """
Email: %s
Phone: %s
Address: %s, %s, %s %s
Total: $%s
Tree: %s
Skirt: %s""" % (email, phone, address, city, state, zipcode, amount / 100, tree_type, skirt_type or '')
    mail.send(msg)

    stripe.Charge.create(
        amount=amount,
        currency='usd',
        card=request.form['stripeToken'],
        description='Tree-Delivery.com - %s | %s' % (email, phone)
    )

    return 'Your order was a success!<br><br>We will give you a call within 24 hours to schedule a delivery. If you have any questions, get in touch with us at the contact information listed at the bottom of <a href="/">Tree-Delivery.com</a>'


@app.route('/email')
def email():
    msg = Message("[Tree-Delivery.com] Test Email", sender=SENDER, recipients=RECIPIENTS)
    msg.body = "test body"
    print 'Mailing...'
    print app.config
    mail.send(msg)
    return 'email sent'


# TODO send an email upon 500 errors


if __name__ == '__main__':
    # Bind to PORT if defined
    port = int(os.environ.get('PORT', 1225))
    debug = not ('heroku' in os.environ.get('PYTHONHOME', ''))
    app.run(host='0.0.0.0', port=port, debug=debug)
