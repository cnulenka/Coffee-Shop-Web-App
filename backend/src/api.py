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

'''
api endpoint to update drinks
'''
@app.route("/drinks/<drink_id>", methods=['PATCH'])
@requires_auth('patch:drinks')
def update_drinks(jwtoken, drink_id):
    body = request.get_json()
    input_title = body.get("title", None)
    input_recipe = body.get("recipe", None)
    drink = Drink.query.filter(Drink.id == drink_id).one_or_none()
    if drink is None:
        abort(404)
    try:
        if input_title:
            drink.title = input_title
        if input_recipe:
            drink.recipe = json.dumps(input_recipe)
        drink.update()
        return jsonify({"success": True, "drink": [drink.long()]}),200
    except:
        abort(422)

'''
api endpoint to delete drink
'''
@app.route("/drinks/<drink_id>", methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drinks(jwtoken, drink_id):
    drink = Drink.query.filter(Drink.id == drink_id).one_or_none()
    if drink is None:
        abort(404)
    try:
        drink.delete()
        return jsonify({"success": True, "delete": drink_id}),200
    except:
        abort(422)

## Error Handling

@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
                    "success": False, 
                    "error": 422,
                    "message": "unprocessable"
                    }), 422

@app.errorhandler(404)
def not_found(error):
    return jsonify({"success": False,
                    "error": 404,
                    "message": "resource not found"
                    }),404

@app.errorhandler(500)
def server_error(error):
    return jsonify({"success": False,
                    "error": 500,
                    "message": "server error"
                    }), 500

@app.errorhandler(401)
def unauthorized(error):
    return jsonify({"success": False,
                    "error": 401,
                    "message": "unauthorized"
                    }), 401

@app.errorhandler(AuthError)
def authorization_error(error):
    return jsonify({
        "success": False,
        "error": error.status_code,
        "message": error.error['description']
    }), error.status_code