"""Save indicators into the DynamoDB instance."""
import boto3
import datetime
import hashlib
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def check_api_key(email, api_key):
    """Check the API key of the user."""
    table = boto3.resource("dynamodb").Table(os.environ['people'])
    user = table.get_item(Key={'email': email})
    if not user:
        return False
    user = user.get("Item")
    if api_key != user.get('api_key', None):
        return False
    return user


def check_role(user):
    """Check the role of the user."""
    if user['role'] not in ['admin', 'researcher']:
        return False
    return True


def lambda_handler(event, context):
    """Main handler."""
    email = event.get('email', None)
    api_key = event.get('api_key', None)
    if not (api_key or email):
        msg = "Missing authentication parameters in your request"
        return {'success': False, 'message': msg}
    indicators = list(set(event.get('indicators', list())))
    if len(indicators) == 0:
        return {'success': False, 'message': "No indicators sent in"}
    user = check_api_key(email, api_key)
    if not user:
        return {'success': False, 'message': "Email or API key was invalid."}
    role = check_role(user)
    if not role:
        return {'success': False, 'message': "Account not approved to contribute."}
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    table = boto3.resource("dynamodb").Table(os.environ['database'])
    with table.batch_writer(overwrite_by_pkeys=['indicator']) as batch:
        for item in indicators:
            if item == "":
                continue
            if len(item) != 32:
                item = hashlib.md5(item).hexdigest()
            try:
                batch.put_item(Item={'indicator': item,
                                     'creator': user.get('email'),
                                     'datetime': current_time})
            except Exception as e:
                logger.error(str(e))

    msg = "Wrote {} indicators".format(len(indicators))
    return {'success': True, 'message': msg, 'writeCount': len(indicators)}
