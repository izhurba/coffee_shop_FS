import os
from turtle import title
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

# ROUTES

# Endpoint to get drinks with short recipe

@app.route('/drinks')
def get_drinks():
    drinks = Drink.query.all()

    if not drinks:
        abort(404)

    return jsonify({
        'success': True,
        'drinks': [drink.short() for drink in drinks]
    }), 200

# Endpoint to get drinks with recipe in full detail

@app.route('/drinks-detail')
@requires_auth('get:drinks-detail')
def get_drink_detailed(jwt):
    try:
        drinks = Drink.query.all()
        
        if not drinks:
            abort(404)
        
        return jsonify({
            'success': True,
            'drinks': [drink.long() for drink in drinks]
        }), 200
        
    except Exception as e:
        print(e)
        abort(AuthError)
        
# Endpoint to create a new drink with a new recipe

@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def post_drinks(jwt):
    data = request.get_json()

    try:
        drink = Drink(
            title = data['title'],
            recipe = json.dumps(data['recipe'])
        )
        drink.insert()

        drinks = Drink.query.all()

        return jsonify({
            'success': True,
            'drinks': [drink.long() for drink in drinks]
        }), 200
    except Exception as e:
        print(e)
        abort(400)
    
# Endpoint to update an existing drink via Drink.id

@app.route('/drinks/<int:id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def patch_drink(jwt, id):
    data = request.get_json()
    drink = Drink.query.get(id)
    try:
        if not drink:
            abort(404)
        if data['title']:
            drink.title = data['title']
        if data['recipe']:
            drink.recipe = json.dumps(list(data['recipe']))
        drink.update()

        drinks = Drink.query.all()

        return jsonify({
            'success': True,
            'drinks': [dk.long() for dk in drinks]
        }),200
    except Exception as e:
        print(e)
        abort(400)

# Endpoint to delete a drink via Drink.id

@app.route('/drinks/<int:id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(jwt, id):
    drink = Drink.query.filter(Drink.id == id).one_or_none()

    if not drink:
        abort(404)
    
    try:
        drink.delete()
        return jsonify({
            'success': True,
            'delete': id
        }), 200
    except Exception as e:
        print(e)
        abort(400)

# Error Handling

@app.errorhandler(400)
def bad_request_error(error):
    return jsonify({
        'success': False,
        'error': 400,
        'message': "Bad Request"
    }), 400

@app.errorhandler(404)
def not_found_error(error):
    return jsonify({
        'success': False,
        'error': 404,
        'message': "Not Found"
        }), 404

@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422

@app.errorhandler(AuthError)
def authorization_error(error):
    return jsonify({
        'success': False,
        'error': AuthError,
        'message': "You are not authorized to perform this action"
        }), 404