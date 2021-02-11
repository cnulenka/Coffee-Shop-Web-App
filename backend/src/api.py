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

# db_drop_and_create_all()

# ROUTES
"""
    The GET /drinks endpoint is a public endpoint that returns
    a list of drinks from the database in the short
    format with a 200 status code
"""


@app.route("/drinks", methods=["GET"])
def get_drinks():
    try:
        drinks = Drink.query.all()
        short_format_drinks = [drink.short() for drink in drinks]
        return jsonify({"success": True, "drinks": short_format_drinks}), 200
    except Exception as error:
        print(error)


"""
The GET /drinks-detail endpoint requires the 'get:drinks-detail' permission.
It returns a list of drinks from the database in the long
format with a 200 status code
"""


@app.route("/drinks-detail", methods=["GET"])
@requires_auth(permission="get:drinks-detail")
def get_drinks_detail(jwtoken):
    try:
        drinks = Drink.query.all()
        long_format_drinks = [drink.long() for drink in drinks]
        return jsonify({"success": True, "drinks": long_format_drinks}), 200
    except AuthError as auth_error:
        print(auth_error)
    except Exception as error:
        print(error)


"""
    The POST /drinks endpoint requires the 'post:drinks' permission.
    It creates a new row in the drinks table with, input is expected
    in long format. returns 422 status code if input data is missing,
    returns the created drink with 200 status. returns 500 if failure
    happens during DB update
"""


@app.route("/drinks", methods=["POST"])
@requires_auth("post:drinks")
def create_drinks(jwtoken):
    try:
        body = request.get_json()
        input_title = body.get("title", None)
        input_recipe = body.get("recipe", None)
        if not input_title or not input_recipe:
            abort(422)
        if type(input_recipe) == str:
            recipe = input_recipe
        else:
            recipe = json.dumps(input_recipe)
        drink = Drink(title=input_title, recipe=recipe)
        drink.insert()
        return jsonify({"success": True, "drink": [drink.long()]}), 200
    except AuthError as auth_error:
        print(auth_error)
    except Exception as error:
        print(error)
        abort(500)


"""
The PATCH /drinks/<int:drink_id> endpoint requires the 'patch:drinks'
permission. drink ID is the expected input param.
If the drink with input ID
can not be found it responds with a 404 error.
If the ID is found, the corresponding row for the ID is updated.
On a successful update, the endpoint returns a 200 code and an array
of drinks, or error 422 in case of DB update failure.
"""


@app.route("/drinks/<drink_id>", methods=["PATCH"])
@requires_auth("patch:drinks")
def update_drinks(jwtoken, drink_id):
    try:
        body = request.get_json()
        input_title = body.get("title", None)
        input_recipe = body.get("recipe", None)
        drink = Drink.query.filter(Drink.id == drink_id).one_or_none()
        if drink is None:
            abort(404)
        if input_title:
            drink.title = input_title
        if input_recipe:
            if type(input_recipe) == str:
                drink.recipe = input_recipe
            else:
                drink.recipe = json.dumps(input_recipe)
        drink.update()
        return jsonify({"success": True, "drinks": [drink.long()]}), 200
    except AuthError as auth_error:
        print(auth_error)
    except Exception as error:
        print(error)
        abort(422)


"""
The DELETE /drinks/<id> endpoint requires the 'delete:drink' permission.
drink ID is the expected input param. If the drink with input ID
can not be found it responds with a 404 error.
If the ID is found then the corresponding row is deleted from the database.
On a successful deletion, the endpoint returns a 200 code and the drink that
was deleted or error 422 in case of DB update failure.
"""


@app.route("/drinks/<drink_id>", methods=["DELETE"])
@requires_auth("delete:drinks")
def delete_drinks(jwtoken, drink_id):
    try:
        drink = Drink.query.filter(Drink.id == drink_id).one_or_none()
        if drink is None:
            abort(404)
        drink.delete()
        return jsonify({"success": True, "delete": drink_id}), 200
    except AuthError as auth_error:
        print(auth_error)
    except Exception as error:
        print(error)
        abort(422)


# Error Handling
"""
    Error handlers to pass message with the error codes
"""


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
                    }), 404


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
    return (
        jsonify(
            {
                "success": False,
                "error": error.status_code,
                "message": error.error["description"],
            }
        ),
        error.status_code,
    )
