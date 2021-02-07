import json
from flask import request, _request_ctx_stack
from functools import wraps
from jose import jwt
from urllib.request import urlopen


AUTH0_DOMAIN = 'dev-krk7h65i.us.auth0.com'
ALGORITHMS = ['RS256']
API_AUDIENCE = 'coffee'

## AuthError Exception
'''
AuthError Exception
A standardized way to communicate auth failure modes
'''
class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


## Auth Header

'''
Get the authorization bearer token from request headers
'''
def get_token_auth_header():
    auth_header = request.headers.get("Authorization", None)
    if not auth_header:
        raise AuthError({
                'code':'authorization_header_not_found',
                'description':'Authorization header must be present.'
            },401)
    auth_header_parts = auth_header.split(' ')
    if auth_header_parts[0].lower() != 'bearer':
        raise AuthError({
                'code':'invalid_authorization_header',
                'description':'Authorization header must start with "Bearer".'
            },401)
    if len(auth_header_parts) == 1:
        raise AuthError({
                'code':'invalid_authorization_header',
                'description':'Authorization header must have a token.'
            },401)
    if len(auth_header_parts) > 2:
        raise AuthError({
                'code':'invalid_authorization_header',
                'description':'Authorization header should be a bearer token.'
            },401)

    return auth_header_parts[1]


'''
Validate claims and verify if desired permissions are included in the payload
'''
def verify_permissions(permission, payload):
    if 'permissions' not in payload:
        raise AuthError({
                'code': 'invalid_claims',
                'description': 'Permissions not found in JWT.'
            }, 400)

    if permission not in payload['permissions']:
        raise AuthError({
                'code': 'unauthorized',
                'description': 'Permission missing.'
            }, 403)

    return True

'''
Verify and decode the jwt and return the payload
'''
def verify_decode_jwt(token):
    jsonurl = urlopen(f'https://{AUTH0_DOMAIN}/.well-known/jwks.json')
    jwks = json.loads(jsonurl.read())
    unverified_header = jwt.get_unverified_header(token)
    rsa_key = {}
    if 'kid' not in unverified_header:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Malformed authorization .'
        }, 401)

    for key in jwks['keys']:
        if key['kid'] == unverified_header['kid']:
            rsa_key = {
                'kty': key['kty'],
                'kid': key['kid'],
                'use': key['use'],
                'n': key['n'],
                'e': key['e']
            }
    if rsa_key:
        try:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=ALGORITHMS,
                audience=API_AUDIENCE,
                issuer='https://' + AUTH0_DOMAIN + '/'
            )

            return payload

        except jwt.ExpiredSignatureError:
            raise AuthError({
                'code': 'token_expired',
                'description': 'Token expired.'
            }, 401)

        except jwt.JWTClaimsError:
            raise AuthError({
                'code': 'invalid_claims',
                'description': 'Please, check the audience and issuer. Invalid claims.'
            }, 401)
        except Exception:
            raise AuthError({
                'code': 'invalid_header',
                'description': 'Unable to parse authentication token.'
            }, 400)
    raise AuthError({
                'code': 'invalid_header',
                'description': 'Unable to find the appropriate key.'
            }, 400)

'''
Decorator to retrieve, verify and decode JWT.
Also validates claims and checks for desried permissions
'''
def requires_auth(permission=''):
    def requires_auth_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            token = get_token_auth_header()
            payload = verify_decode_jwt(token)
            verify_permissions(permission, payload)
            return f(payload, *args, **kwargs)

        return wrapper
    return requires_auth_decorator