"""Automatically setup the AWS infrastructure needed for Blockade.io."""
import boto3
import json
import logging
import os
import random
import requests
import sys
import time
from argparse import ArgumentParser
from builtins import input

logger = logging.getLogger("BLOCKADE_SERVERLESS")
logger.setLevel(logging.INFO)
shandler = logging.StreamHandler(sys.stdout)
fmt = '\033[1;32m%(levelname)-5s %(module)s:%(funcName)s():'
fmt += '%(lineno)d %(asctime)s\033[0m| %(message)s'
shandler.setFormatter(logging.Formatter(fmt))
logger.addHandler(shandler)


PRIMARY_REGION = "us-west-1"
BLOCKADE_USER = "blockade"
BLOCKADE_ROLE = "Blockade_Maintainer"
BLOCKADE_GROUP = "Blockade_Admins"
S3_BUCKET_ID = "%d%d" % (random.randint(10000, 99999),
                         random.randint(10000, 99999))
S3_BUCKET_NAME = "blockade-records"
S3_BUCKET = '-'.join([S3_BUCKET_NAME, S3_BUCKET_ID])
ANALYST_TOOLBENCH = "https://github.com/blockadeio/analyst_toolbench"
CLOUD_NODE_DOCS = "https://github.com/blockadeio/cloud_node"
API_GATEWAY = 'Blockade_API'
SUPPORTED_REGIONS = ['us-west-1', 'us-west-2', 'us-east-1', 'us-east-2']
DYNAMODB_TABLES = ['blockade_users', 'blockade_events', 'blockade_indicators']
DYNAMODB_SCHEMAS = {
    'blockade_users': {
        'KeySchema': [{
            'AttributeName': 'email',
            'KeyType': 'HASH'
        }],
        'AttributeDefinitions': [{
            'AttributeName': 'email',
            'AttributeType': 'S'
        }]
    },
    'blockade_events': {
        'KeySchema': [{
            'AttributeName': 'indicatorMatch',
            'KeyType': 'HASH'
        }, {
            'AttributeName': 'event',
            'KeyType': 'RANGE'
        }],
        'AttributeDefinitions': [{
            'AttributeName': 'indicatorMatch',
            'AttributeType': 'S'
        }, {
            'AttributeName': 'event',
            'AttributeType': 'S'
        }]
    },
    'blockade_indicators': {
        'KeySchema': [{
            'AttributeName': 'indicator',
            'KeyType': 'HASH'
        }, {
            'AttributeName': 'creator',
            'KeyType': 'RANGE'
        }],
        'AttributeDefinitions': [{
            'AttributeName': 'indicator',
            'AttributeType': 'S'
        }, {
            'AttributeName': 'creator',
            'AttributeType': 'S'
        }]
    }
}
LAMBDA_FUNCTIONS = ['Blockade-Get-Indicators', 'Blockade-Add-Indicators',
                    'Blockade-Store-Events', 'Blockade-Add-User',
                    'Blockade-Get-Events']
LAMBDA_SCHEMA = {
    'Blockade-Get-Indicators': {
        'FunctionName': 'Blockade-Get-Indicators',
        'Description': 'Get indicators from Blockade',
        'Handler': 'Blockade-Get-Indicators.lambda_handler',
        'Environment': {
            'Variables': {
                'database': 'blockade_indicators'
            }
        }
    },
    'Blockade-Add-Indicators': {
        'FunctionName': 'Blockade-Add-Indicators',
        'Description': 'Add indicators into the Blockade database',
        'Handler': 'Blockade-Add-Indicators.lambda_handler',
        'Environment': {
            'Variables': {
                'database': 'blockade_indicators',
                'people': 'blockade_users'
            }
        }
    },
    'Blockade-Store-Events': {
        'FunctionName': 'Blockade-Store-Events',
        'Description': 'Store event information from Blockade nodes',
        'Handler': 'Blockade-Store-Events.lambda_handler',
        'Environment': {
            'Variables': {
                'database': 'blockade_events',
                's3_bucket': S3_BUCKET
            }
        }
    },
    'Blockade-Add-User': {
        'FunctionName': 'Blockade-Add-User',
        'Description': 'Add users to the Blockade database',
        'Handler': 'Blockade-Add-User.lambda_handler',
        'Environment': {
            'Variables': {
                'people': 'blockade_users'
            }
        }
    },
    'Blockade-Get-Events': {
        'FunctionName': 'Blockade-Get-Events',
        'Description': 'Get events from the Blockade database',
        'Handler': 'Blockade-Get-Events.lambda_handler',
        'Environment': {
            'Variables': {
                'people': 'blockade_users',
                'database': 'blockade_events'
            }
        }
    }
}
API_GATEWAY_RESOURCES = ['Blockade-Get-Indicators', 'Blockade-Store-Events',
                         'Blockade-Add-Indicators', 'Blockade-Add-User',
                         'Blockade-Get-Events']
API_GATEWAY_RESOURCE_SCHEMA = {
    'Blockade-Get-Indicators': {
        'admin': False,
        'resource': {
            'path': 'get-indicators',
            'method': 'GET'
        },
        'request': {
            'template': {
                'application/json': ''
            }
        },
        'response': {
            'template': {
                'application/json': ''
            }
        }
    },
    'Blockade-Store-Events': {
        'admin': False,
        'resource': {
            'path': 'send-events',
            'method': 'POST'
        },
        'request': {
            'template': {
                'application/json': '{"source_ip" : "$context.identity.sourceIp", "body" : $input.json(\'$\')}'
            }
        },
        'response': {
            'template': {
                'application/json': ''
            }
        }
    },
    'Blockade-Add-Indicators': {
        'admin': True,
        'resource': {
            'path': 'add-indicators',
            'method': 'POST'
        },
        'request': {
            'template': {
                'application/json': ''
            }
        },
        'response': {
            'template': {
                'application/json': ''
            }
        }
    },
    'Blockade-Add-User': {
        'admin': True,
        'resource': {
            'path': 'add-user',
            'method': 'POST'
        },
        'request': {
            'template': {
                'application/json': ''
            }
        },
        'response': {
            'template': {
                'application/json': ''
            }
        }
    },
    'Blockade-Get-Events': {
        'admin': True,
        'resource': {
            'path': 'get-events',
            'method': 'POST'
        },
        'request': {
            'template': {
                'application/json': ''
            }
        },
        'response': {
            'template': {
                'application/json': ''
            }
        }
    }
}

BLOCKADE_ROLE_POLICY = '{\
  "Version": "2012-10-17",\
  "Statement": [\
    {\
      "Effect": "Allow",\
      "Principal": {\
        "Service": "lambda.amazonaws.com"\
      },\
      "Action": "sts:AssumeRole"\
    },\
    {\
      "Effect": "Allow",\
      "Principal": {\
        "Service": "apigateway.amazonaws.com"\
      },\
      "Action": "sts:AssumeRole"\
    }\
  ]\
}'

BLOCKADE_POLICIES = ['Blockade_API_Gateway', 'Blockade_CloudWatch',
                     'Blockade_DynamoDB', 'Blockade_IAM', 'Blockade_Lambda',
                     'Blockade_S3']
POLICIES = {
    'Blockade_API_Gateway': '{\
        "Version": "2012-10-17",\
        "Statement": [\
            {\
                "Sid": "VisualEditor0",\
                "Effect": "Allow",\
                "Action": [\
                    "apigateway:DELETE",\
                    "apigateway:PUT",\
                    "apigateway:HEAD",\
                    "apigateway:PATCH",\
                    "apigateway:POST",\
                    "apigateway:GET",\
                    "apigateway:OPTIONS"\
                ],\
                "Resource": "arn:aws:apigateway:*::/*"\
            }\
        ]\
    }',
    'Blockade_CloudWatch': '{\
        "Version": "2012-10-17",\
        "Statement": [\
            {\
                "Sid": "VisualEditor0",\
                "Effect": "Allow",\
                "Action": "logs:*",\
                "Resource": "*"\
            }\
        ]\
    }',
    'Blockade_DynamoDB': '{\
        "Version": "2012-10-17",\
        "Statement": [\
            {\
                "Sid": "VisualEditor0",\
                "Effect": "Allow",\
                "Action": [\
                    "dynamodb:CreateTable",\
                    "dynamodb:BatchGetItem",\
                    "dynamodb:BatchWriteItem",\
                    "dynamodb:PutItem",\
                    "dynamodb:DeleteItem",\
                    "dynamodb:GetItem",\
                    "dynamodb:Scan",\
                    "dynamodb:Query",\
                    "dynamodb:UpdateItem",\
                    "dynamodb:DeleteTable",\
                    "dynamodb:UpdateTable",\
                    "dynamodb:GetRecords",\
                    "dynamodb:DescribeTable"\
                ],\
                "Resource": [\
                    "arn:aws:dynamodb:*:*:table/blockade_events",\
                    "arn:aws:dynamodb:*:*:table/blockade_indicators",\
                    "arn:aws:dynamodb:*:*:table/blockade_users"\
                ]\
            },\
            {\
                "Sid": "VisualEditor1",\
                "Effect": "Allow",\
                "Action": "dynamodb:ListTables",\
                "Resource": "*"\
            }\
        ]\
    }',
    'Blockade_IAM': '{\
        "Version": "2012-10-17",\
        "Statement": [\
            {\
                "Sid": "VisualEditor0",\
                "Effect": "Allow",\
                "Action": [\
                    "iam:PassRole",\
                    "iam:GetUser"\
                ],\
                "Resource": [\
                    "arn:aws:iam::*:user/blockade",\
                    "arn:aws:iam::*:role/Blockade_Control"\
                ]\
            }\
        ]\
    }',
    'Blockade_Lambda': '{\
        "Version": "2012-10-17",\
        "Statement": [\
            {\
                "Sid": "VisualEditor0",\
                "Effect": "Allow",\
                "Action": [\
                    "lambda:CreateFunction",\
                    "lambda:UpdateFunctionCode",\
                    "lambda:ListFunctions",\
                    "lambda:InvokeFunction",\
                    "lambda:GetFunction",\
                    "lambda:UpdateFunctionConfiguration",\
                    "lambda:InvokeAsync",\
                    "lambda:DeleteFunction",\
                    "lambda:PublishVersion",\
                    "lambda:Invoke",\
                    "lambda:AddPermission"\
                ],\
                "Resource": "*"\
            }\
        ]\
    }',
    'Blockade_S3': '{\
        "Version": "2012-10-17",\
        "Statement": [\
            {\
                "Sid": "VisualEditor0",\
                "Effect": "Allow",\
                "Action": [\
                    "s3:PutObject",\
                    "s3:CreateBucket",\
                    "s3:ListBucket",\
                    "s3:DeleteObject",\
                    "s3:DeleteBucket"\
                ],\
                "Resource": [\
                    "arn:aws:s3:::%s/*",\
                    "arn:aws:s3:::%s"\
                ]\
            },\
            {\
                "Sid": "VisualEditor1",\
                "Effect": "Allow",\
                "Action": [\
                    "s3:ListAllMyBuckets",\
                    "s3:ListObjects"\
                ],\
                "Resource": "*"\
            }\
        ]\
    }' % (S3_BUCKET, S3_BUCKET)
}


def generate_handler():
    """Create the Blockade user and give them permissions."""
    logger.debug("[#] Setting up user, group and permissions")
    client = boto3.client("iam", region_name=PRIMARY_REGION)

    # Create the user
    try:
        response = client.create_user(
            UserName=BLOCKADE_USER
        )
    except client.exceptions.EntityAlreadyExistsException:
        logger.debug("[!] Blockade user already exists")
    logger.info("[#] %s user successfully created" % (BLOCKADE_USER))

    # Create the role
    try:
        logger.debug("[#] Creating %s role" % (BLOCKADE_ROLE))
        response = client.create_role(
            RoleName=BLOCKADE_ROLE,
            AssumeRolePolicyDocument=BLOCKADE_ROLE_POLICY,
            Description="Allow a user to manage the administration of Blockade."
        )
    except client.exceptions.EntityAlreadyExistsException:
        logger.debug("[!] Blockade role already exists")
    logger.info("[#] %s role successfully created" % (BLOCKADE_ROLE))

    # Create the group
    try:
        logger.debug("[#] Creating %s group" % (BLOCKADE_GROUP))
        response = client.create_group(
            GroupName=BLOCKADE_GROUP,
        )
    except client.exceptions.EntityAlreadyExistsException:
        logger.debug("[!] Blockade group already exists")
    logger.info("[#] %s group successfully created" % (BLOCKADE_GROUP))

    # Generate all policy items
    logger.debug("[#] Creating Blockade IAM policies")
    for label in BLOCKADE_POLICIES:
        logger.debug("[#] Creating %s policy" % (label))
        try:
            response = client.create_policy(
                PolicyName=label,
                PolicyDocument=POLICIES[label],
                Description="Generated policy from Blockade bootstrap tool"
            )
        except client.exceptions.EntityAlreadyExistsException:
            logger.debug("[!] Blockade policy %s already exists" % (label))
        logger.info("[#] Blockade %s policy successfully created" % (label))
    logger.info("[#] Blockade policies successfully created")

    # Attach policies to all entity types
    iam = boto3.resource('iam')
    account_id = iam.CurrentUser().arn.split(':')[4]
    for label in BLOCKADE_POLICIES + ['PushToCloud', 'APIGatewayAdmin']:
        logger.debug("[#] Attaching %s policy" % (label))
        arn = 'arn:aws:iam::{id}:policy/{policy}'.format(id=account_id, policy=label)
        if label == 'PushToCloud':
            arn = "arn:aws:iam::aws:policy/service-role/AmazonAPIGatewayPushToCloudWatchLogs"
        if label == 'APIGatewayAdmin':
            arn = "arn:aws:iam::aws:policy/AmazonAPIGatewayAdministrator"
        client.attach_role_policy(RoleName=BLOCKADE_ROLE, PolicyArn=arn)
        client.attach_group_policy(GroupName=BLOCKADE_GROUP, PolicyArn=arn)
    logger.info("[#] Blockade policies successfully attached")

    logger.debug("[#] Adding %s to %s group" % (BLOCKADE_USER, BLOCKADE_GROUP))
    response = client.add_user_to_group(
        GroupName=BLOCKADE_GROUP,
        UserName=BLOCKADE_USER
    )
    logger.info("[#] %s user is part of %s group" % (BLOCKADE_USER, BLOCKADE_GROUP))

    return True


def remove_handler():
    """Remove the user, group and policies for Blockade."""
    logger.debug("[#] Removing user, group and permissions for Blockade")
    client = boto3.client("iam", region_name=PRIMARY_REGION)

    iam = boto3.resource('iam')
    account_id = iam.CurrentUser().arn.split(':')[4]

    try:
        logger.debug("[#] Removing %s from %s group" % (BLOCKADE_USER, BLOCKADE_GROUP))
        response = client.remove_user_from_group(
            GroupName=BLOCKADE_GROUP,
            UserName=BLOCKADE_USER
        )
    except client.exceptions.NoSuchEntityException:
        logger.debug("[!] Blockade user already removed from group")

    for label in BLOCKADE_POLICIES + ['PushToCloud', 'APIGatewayAdmin']:
        logger.debug("[#] Removing %s policy" % (label))
        arn = 'arn:aws:iam::{id}:policy/{policy}'.format(id=account_id,
                                                         policy=label)
        if label == 'PushToCloud':
            arn = "arn:aws:iam::aws:policy/service-role/AmazonAPIGatewayPushToCloudWatchLogs"
        if label == 'APIGatewayAdmin':
            arn = "arn:aws:iam::aws:policy/AmazonAPIGatewayAdministrator"

        try:
            response = client.detach_group_policy(
                GroupName=BLOCKADE_GROUP, PolicyArn=arn)
        except:
            pass
        try:
            response = client.detach_role_policy(
                RoleName=BLOCKADE_ROLE, PolicyArn=arn)
        except:
            pass
        try:
            response = client.delete_policy(PolicyArn=arn)
        except Exception as e:
            print(e)
            pass
    logger.debug("[#] Removed all policies")

    try:
        logger.debug("[#] Deleting %s user" % (BLOCKADE_USER))
        response = client.delete_user(
            UserName=BLOCKADE_USER
        )
    except client.exceptions.NoSuchEntityException:
        logger.debug("[!] %s user already deleted" % (BLOCKADE_USER))

    try:
        logger.debug("[#] Removing %s group" % (BLOCKADE_GROUP))
        response = client.delete_group(GroupName=BLOCKADE_GROUP)
    except:
        logger.debug("[!] Group already removed")

    try:
        logger.debug("[#] Removing %s role" % (BLOCKADE_ROLE))
        response = client.delete_role(RoleName=BLOCKADE_ROLE)
    except:
        logger.debug("[!] Role already removed")

    return True


def generate_s3_bucket():
    """Create the blockade bucket if not already there."""
    logger.debug("[#] Setting up S3 bucket")
    client = boto3.client("s3", region_name=PRIMARY_REGION)
    buckets = client.list_buckets()
    matches = [x for x in buckets.get('Buckets', list())
               if x['Name'].startswith(S3_BUCKET)]
    if len(matches) > 0:
        logger.debug("[*] Bucket already exists")
        return matches.pop()

    response = client.create_bucket(
        Bucket=S3_BUCKET,
        CreateBucketConfiguration={
            'LocationConstraint': PRIMARY_REGION
        }
    )
    logger.info("[#] Successfully setup the S3 bucket")

    return response


def remove_s3_bucket():
    """Remove the Blockade bucket."""
    logger.debug("[#] Removing S3 bucket")
    client = boto3.client("s3", region_name=PRIMARY_REGION)
    buckets = client.list_buckets()
    matches = [x for x in buckets.get('Buckets', list())
               if x['Name'].startswith(S3_BUCKET_NAME)]
    if len(matches) == 0:
        return
    match = matches.pop()['Name']
    try:
        response = client.list_objects_v2(
            Bucket=match,
        )
    except client.exceptions.NoSuchBucket:
        logger.info("[!] S3 bucket already deleted")
        return True

    while response['KeyCount'] > 0:
        logger.debug('[*] Deleting %d objects from bucket %s'
                     % (len(response['Contents']), match))
        response = client.delete_objects(
            Bucket=match,
            Delete={
                'Objects': [{'Key': obj['Key']} for obj in response['Contents']]
            }
        )
        response = client.list_objects_v2(
            Bucket=match,
        )

    logger.debug('[#] Deleting bucket %s' % match)
    response = client.delete_bucket(
        Bucket=match
    )
    logger.info("[#] Successfully deleted the S3 bucket")

    return response


def generate_dynamodb_tables():
    """Create the Blockade DynamoDB tables."""
    logger.debug("[#] Setting up DynamoDB tables")
    client = boto3.client('dynamodb', region_name=PRIMARY_REGION)
    existing_tables = client.list_tables()['TableNames']

    responses = list()
    for label in DYNAMODB_TABLES:
        if label in existing_tables:
            logger.debug("[*] Table %s already exists" % (label))
            continue

        kwargs = {
            'TableName': label,
            'ProvisionedThroughput': {
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        }
        kwargs.update(DYNAMODB_SCHEMAS[label])
        response = client.create_table(**kwargs)
        responses.append(response)
        logger.debug("[#] Successfully setup DynamoDB table %s" % (label))
    logger.info("[#] Successfully setup DynamoDB tables")

    return responses


def remove_dynamodb_tables():
    """Remove the Blockade DynamoDB tables."""
    logger.debug("[#] Removing DynamoDB tables")
    client = boto3.client('dynamodb', region_name=PRIMARY_REGION)

    responses = list()
    for label in DYNAMODB_TABLES:
        logger.debug("[*] Removing %s table" % (label))
        try:
            response = client.delete_table(
                TableName=label
            )
        except client.exceptions.ResourceNotFoundException:
            logger.info("[!] Table %s already removed" % (label))
            continue
        responses.append(response)
        logger.debug("[*] Removed %s table" % (label))
    logger.info("[#] Successfully removed DynamoDB tables")

    return responses


def generate_lambda_functions():
    """Create the Blockade lambda functions."""
    logger.debug("[#] Setting up the Lambda functions")
    aws_lambda = boto3.client('lambda', region_name=PRIMARY_REGION)
    functions = aws_lambda.list_functions().get('Functions')
    existing_funcs = [x['FunctionName'] for x in functions]

    iam = boto3.resource('iam')
    account_id = iam.CurrentUser().arn.split(':')[4]

    responses = list()
    for label in LAMBDA_FUNCTIONS:
        if label in existing_funcs:
            logger.debug("[*] Lambda function %s already exists" % (label))
            continue
        dir_path = os.path.dirname(os.path.realpath(__file__))
        dir_path = dir_path.replace('/cli', '/aws')

        kwargs = {
            'Runtime': 'python2.7',
            'Role': 'arn:aws:iam::{0}:role/{1}'.format(account_id, BLOCKADE_ROLE),
            'Timeout': 3,
            'MemorySize': 128,
            'Publish': True,
            'Code': {
                'ZipFile': open("{0}/lambda-zips/{1}.zip".format(dir_path, label), 'rb').read()
            }
        }
        kwargs.update(LAMBDA_SCHEMA[label])
        logger.debug("[#] Setting up the %s Lambda function" % (label))
        response = aws_lambda.create_function(**kwargs)
        responses.append(response)
        logger.debug("[#] Successfully setup Lambda function %s" % (label))
    logger.info("[#] Successfully setup Lambda functions")

    return responses


def remove_lambda_functions():
    """Remove the Blockade Lambda functions."""
    logger.debug("[#] Removing the Lambda functions")
    client = boto3.client('lambda', region_name=PRIMARY_REGION)

    responses = list()
    for label in LAMBDA_FUNCTIONS:
        try:
            response = client.delete_function(
                FunctionName=label,
            )
        except client.exceptions.ResourceNotFoundException:
            logger.info("[!] Function %s already removed" % (label))
            continue
        responses.append(response)
        logger.debug("[*] Removed %s function" % (label))
    logger.info("[#] Successfully removed Lambda functions")

    return responses


def generate_api_gateway():
    """Create the Blockade API Gateway REST service."""
    logger.debug("[#] Setting up the API Gateway")
    client = boto3.client('apigateway', region_name=PRIMARY_REGION)
    matches = [x for x in client.get_rest_apis().get('items', list())
               if x['name'] == API_GATEWAY]
    if len(matches) > 0:
        logger.debug("[#] API Gateway already setup")
        return matches.pop()

    response = client.create_rest_api(
        name=API_GATEWAY,
        description='REST-API to power the Blockade service'
    )
    logger.info("[#] Successfully setup the API Gateway")

    return response


def generate_admin_resource():
    """Create the Blockade admin resource for the REST services."""
    logger.debug("[#] Setting up the admin resource")
    client = boto3.client('apigateway', region_name=PRIMARY_REGION)
    existing = get_api_gateway_resource("admin")
    if existing:
        logger.debug("[#] API admin resource already created")
        return True
    matches = [x for x in client.get_rest_apis().get('items', list())
               if x['name'] == API_GATEWAY]
    match = matches.pop()
    resource_id = get_api_gateway_resource('/')
    response = client.create_resource(
        restApiId=match.get('id'),
        parentId=resource_id,
        pathPart='admin'
    )
    logger.info("[#] Successfully setup the admin resource")

    return response


def get_api_gateway_resource(name):
    """Get the resource associated with our gateway."""
    client = boto3.client('apigateway', region_name=PRIMARY_REGION)
    matches = [x for x in client.get_rest_apis().get('items', list())
               if x['name'] == API_GATEWAY]
    match = matches.pop()
    resources = client.get_resources(restApiId=match.get('id'))
    resource_id = None
    for item in resources.get('items', list()):
        if item.get('pathPart', '/') != name:
            continue
        resource_id = item['id']
    return resource_id


def generate_api_resources():
    """Generate the Blockade API endpoints."""
    client = boto3.client('apigateway', region_name=PRIMARY_REGION)
    matches = [x for x in client.get_rest_apis().get('items', list())
               if x['name'] == API_GATEWAY]
    match = matches.pop()

    iam = boto3.resource('iam')
    account_id = iam.CurrentUser().arn.split(':')[4]

    for label in API_GATEWAY_RESOURCES:
        schema = API_GATEWAY_RESOURCE_SCHEMA[label]
        existing = get_api_gateway_resource(schema['resource']['path'])
        if existing:
            logger.debug("[#] API resource %s already created" % (label))
            continue

        resource_id = get_api_gateway_resource('/')
        if schema['admin']:
            resource_id = get_api_gateway_resource('admin')

        logger.debug("[#] Adding %s endpoint" % (label))
        schema = API_GATEWAY_RESOURCE_SCHEMA[label]

        logger.debug("[#] Creating %s resource" % (schema['resource']['path']))
        resource = client.create_resource(
            restApiId=match.get('id'),
            parentId=resource_id,
            pathPart=schema['resource']['path']
        )
        logger.debug("[#] Created %s resource" % (schema['resource']['path']))

        logger.debug("[#] Creating %s method" % (schema['resource']['method']))
        method = client.put_method(
            restApiId=match.get('id'),
            resourceId=resource.get('id'),
            httpMethod=schema['resource']['method'],
            authorizationType='NONE'
        )
        logger.debug("[#] Created %s method" % (schema['resource']['method']))

        logger.debug("[#] Creating %s integration" % (label))
        uri = "arn:aws:apigateway:{region}:lambda:path/2015-03-31/functions/"
        uri += "arn:aws:lambda:{region}:{id}:function:{func}/invocations"
        integration = client.put_integration(
            restApiId=match.get('id'),
            resourceId=resource.get('id'),
            httpMethod=schema['resource']['method'],
            type='AWS',
            integrationHttpMethod='POST',
            uri=uri.format(id=account_id, region=PRIMARY_REGION, func=label),
            requestTemplates=schema['request']['template'],
            passthroughBehavior='WHEN_NO_TEMPLATES'
        )
        logger.debug("[#] Created %s integration" % (label))

        logger.debug("[#] Creating %s response method" % (label))
        method_reponse = client.put_method_response(
            restApiId=match.get('id'),
            resourceId=resource.get('id'),
            httpMethod=schema['resource']['method'],
            statusCode='200'
        )
        logger.debug("[#] Created %s response method" % (label))

        logger.debug("[#] Creating %s integration response" % (label))
        integration_response = client.put_integration_response(
            restApiId=match.get('id'),
            resourceId=resource.get('id'),
            httpMethod=schema['resource']['method'],
            statusCode='200',
            responseTemplates=schema['response']['template']
        )
        logger.debug("[#] Created %s integration response" % (label))

        logger.debug("[#] Generating %s permissions" % (label))
        aws_lambda = boto3.client('lambda', region_name=PRIMARY_REGION)

        if not schema['admin']:
            arn = "arn:aws:execute-api:{region}:{account_id}:{rest_id}/*/{method}/{path}"
        else:
            arn = "arn:aws:execute-api:{region}:{account_id}:{rest_id}/*/{method}/admin/{path}"
        aws_lambda.add_permission(
            FunctionName=label,
            StatementId='BlockadeBootstrap-%d' % (random.randint(0, 9999)),
            Action='lambda:InvokeFunction',
            Principal='apigateway.amazonaws.com',
            SourceArn=arn.format(region=PRIMARY_REGION, account_id=account_id,
                                 rest_id=match.get('id'),
                                 method=schema['resource']['method'],
                                 path=schema['resource']['path'])
        )
        logger.debug("[#] Generated %s permissions" % (label))

    logger.debug("[#] Creating production deployment")
    deployment = client.create_deployment(
        restApiId=match.get('id'),
        stageName='prod'
    )
    url = "https://{rest_id}.execute-api.{region}.amazonaws.com/prod/"
    url = url.format(rest_id=match.get('id'), region=PRIMARY_REGION)
    logger.debug("[#] Deployment is accessible: %s" % (url))

    return url


def remove_api_gateway():
    """Remove the Blockade REST API service."""
    logger.debug("[#] Removing API Gateway")
    client = boto3.client('apigateway', region_name=PRIMARY_REGION)
    matches = [x for x in client.get_rest_apis().get('items', list())
               if x['name'] == API_GATEWAY]
    if len(matches) == 0:
        logger.info("[!] API Gateway already removed")
        return True
    match = matches.pop()
    response = client.delete_rest_api(
        restApiId=match.get('id')
    )
    logger.info("[#] Removed API Gateway")

    return response


def main():
    """Run along little fella."""
    parser = ArgumentParser()
    subs = parser.add_subparsers(dest='cmd')
    setup_parser = subs.add_parser('setup')
    setup_parser.add_argument('-r', '--region', default=PRIMARY_REGION,
                              help='AWS region to install all services')
    setup_parser.add_argument('-d', '--debug', action='store_true',
                              help='Run in debug mode')
    setup_parser.add_argument('--rollback', action='store_true',
                              help='Rollback configuration on failure')
    setup_parser.add_argument('--skip-node-setup', action='store_true',
                              help='Rollback configuration on failure')
    setup_parser = subs.add_parser('teardown')
    setup_parser.add_argument('-r', '--region', default=PRIMARY_REGION,
                              help='AWS region to delete all services')
    setup_parser.add_argument('-d', '--debug', action='store_true',
                              help='Run in debug mode')
    args = parser.parse_args()

    if args.region:
        if args.region not in SUPPORTED_REGIONS:
            raise Exception("INVALID_REGION: Region must be one of: %s"
                            % (', '.join(SUPPORTED_REGIONS)))
        global PRIMARY_REGION
        PRIMARY_REGION = args.region

    if args.debug:
        logger.setLevel(logging.DEBUG)

    if args.cmd == 'setup':
        try:
            generate_handler()
            time.sleep(7)
            generate_s3_bucket()
            generate_dynamodb_tables()
            generate_lambda_functions()
            generate_api_gateway()
            generate_admin_resource()
            api_node = generate_api_resources()
        except Exception as e:
            logger.error(str(e))
            if args.rollback:
                logger.info("[!] Rolling back deployed services")
                remove_s3_bucket()
                remove_dynamodb_tables()
                remove_lambda_functions()
                remove_api_gateway()
                remove_handler()

        if not args.skip_node_setup:
            email = input("[*] Blockade admin email: ")
            if email.find('@') < 0:
                logger.error("[!] %s does not appear to be an email" % email)
                email = input("[*] Blockade admin email: ")
            name = input("[*] Blockade admin name: ")

            url = api_node + "admin/add-user"
            params = {'user_email': email, 'user_name': name,
                      'user_role': 'admin'}
            headers = {'Content-Type': 'application/json'}
            response = requests.post(url, data=json.dumps(params),
                                     headers=headers)
            loaded = json.loads(response.content)
            logger.info("[#] Successfully added Blockade admin")
            logger.debug(loaded)
            print("---------------------------------------------------------------------------")
            print("Blockade Server: %s" % api_node)
            print("Blockade Admin: %s" % loaded['email'])
            print("Blockade API Key: %s" % loaded['api_key'])
            print("---------------------------------------------------------------------------")
            print("Quick Config: blockade-cfg setup %s %s --api-node=%s"
                  % (loaded['email'], loaded['api_key'], api_node))
            print("Next steps: Add indicators to your node with our analyst toolbench: %s" % (ANALYST_TOOLBENCH))
            print("For more documentation on other cloud node actions, see %s." % (CLOUD_NODE_DOCS))

    if args.cmd == 'teardown':
        remove_s3_bucket()
        remove_dynamodb_tables()
        remove_lambda_functions()
        remove_api_gateway()
        remove_handler()


if __name__ == "__main__":
    main()
