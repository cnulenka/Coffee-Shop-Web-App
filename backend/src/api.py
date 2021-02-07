import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

db_drop_and_create_all()

## ROUTES
'''
api endpoint to get all drinks
'''
@app.route("/drinks", methods=["GET"])
def get_drinks():
    drinks = Drink.query.all()
    short_format_drinks = [drink.short() for drink in drinks]
    return jsonify({"success": True, "drinks": short_format_drinks}),200



'''
api endpoint to get all drinks in details
'''
@app.route("/drinks-detail", methods=['GET'])
@requires_auth(permission='get:drinks-detail')
def get_drink_detail(jwtoken):
    drinks = Drink.query.all()
    long_format_drinks = [drink.long() for drink in drinks]
    return jsonify({"success": True, "drinks": long_format_drinks}),200


'''
api endpoint to create new drinks
'''
@app.route("/drinks", methods=['POST'])
@requires_auth('post:drinks')
def create_drinks(jwtoken):
    body = request.get_json()
    input_title = body.get("title", None)
    input_recipe = body.get("recipe", None)
    if not input_title or not input_recipe:
        abort(422)
    try:
        drink = Drink(title = input_title, recipe = json.dumps(input_recipe))
        drink.insert()
        return jsonify({"success": True, "drink": [drink.long()]}),200
    except:
        abort(500)

