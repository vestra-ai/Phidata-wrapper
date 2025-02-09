from functools import wraps
from flask import request, jsonify
import jwt
import os

SECRET_KEY = os.environ.get('JWT_SECRET_KEY')

def jwt_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if 'Authorization' in request.headers:
            auth_header = request.headers.get('Authorization')
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({'message': 'Invalid token format'}), 401

        if not token:
            return jsonify({'message': 'Token is missing'}), 401

        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            user_id=payload['sub']['user_id']
            if not user_id:
                return jsonify({'message': 'user id not found'}), 401
    
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token'}), 401
        
        request.user_id = user_id
        return f(*args, **kwargs)

    return decorated
