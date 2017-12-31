"""Get indicators from the DynamoDB instance."""
import boto3
import os


def lambda_handler(event, context):
    """Main handler."""
    table = boto3.resource("dynamodb").Table(os.environ['database'])
    results = table.scan()
    output = {'success': True, 'indicators': list(), 'indicatorCount': 0}
    for item in results.get('Items', list()):
        indicator = item.get('indicator', None)
        if not indicator:
            continue
        output['indicators'].append(indicator)
    output['indicators'] = list(set(output['indicators']))
    output['indicatorCount'] = len(output['indicators'])
    return output
