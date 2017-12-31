"""Get indicators from the DynamoDB instance."""
import boto3
import hashlib
import os
import random


def check_auth(args, role=None):
    """Check the user authentication."""
    users = boto3.resource("dynamodb").Table(os.environ['people'])
    response = users.scan()
    if response['Count'] == 0:
        return {'success': True, 'message': None, 'init': True}
    if not (args.get('email', None) and args.get('api_key', None)):
        mesg = "Invalid request: `email` and `api_key` are required"
        return {'success': False, 'message': mesg}
    user = users.get_item(Key={'email': args.get('email')})
    if 'Item' not in user:
        return {'success': False, 'message': 'User does not exist.'}
    user = user['Item']
    if user['api_key'] != args['api_key']:
        return {'success': False, 'message': 'API key was invalid.'}
    if role:
        if user['role'] not in role:
            mesg = 'User is not authorized to make this change.'
            return {'success': False, 'message': mesg}
    return {'success': True, 'message': None, 'user': user}


def lambda_handler(event, context):
    """Main handler."""
    users = boto3.resource("dynamodb").Table(os.environ['people'])
    auth = check_auth(event, role=["admin"])
    if not auth['success']:
        return auth
    user_email = event.get('user_email', None)
    if not user_email:
        msg = "Missing user_email parameter in your request."
        return {'success': False, 'message': msg}
    user_role = event.get('user_role', None)
    if not user_role:
        msg = "Missing user role: `admin`, `analyst`"
        return {'success': False, 'message': msg}
    user_name = event.get('user_name', '')
    seed = random.randint(100000000, 999999999)
    hash_key = "{}{}".format(user_email, seed)
    api_key = hashlib.sha256(hash_key).hexdigest()
    if auth.get('init', False):
        user_role = 'admin'
    else:
        user_role = user_role
    obj = {'email': user_email, 'name': user_name, 'api_key': api_key,
           'role': user_role}
    response = users.put_item(Item=obj)
    return obj


