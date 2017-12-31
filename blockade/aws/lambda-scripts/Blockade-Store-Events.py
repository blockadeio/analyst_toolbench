"""Save event data from alert hits locally."""
import boto3
import json
import hashlib
import logging
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def convert_keys_to_string(dictionary):
    """Recursively converts dictionary keys to strings."""
    if not isinstance(dictionary, dict):
        return dictionary
    return dict((str(k), convert_keys_to_string(v))
        for k, v in dictionary.items())


def process_events(events, source_ip):
    """Process all the events for logging and S3."""
    s3 = boto3.resource('s3')
    table = boto3.resource("dynamodb").Table(os.environ['database'])
    with table.batch_writer() as batch:
        for idx, event in enumerate(events):
            event = convert_keys_to_string(event)
            event['sourceIp'] = source_ip
            event['event'] = hashlib.sha256(str(event)).hexdigest()
            metadata = event['metadata']
            timestamp = str(event['metadata']['timeStamp'])
            event['metadata']['timeStamp'] = timestamp
            kwargs = {'match': event['indicatorMatch'],
                      'type': metadata['type'],
                      'method': metadata['method'].lower(),
                      'time': event['analysisTime'], 'ip': source_ip}
            file_struct = '{match}_{type}_{method}_{ip}_{time}.json'
            file_name = file_struct.format(**kwargs)
            key_path = '/tmp/%s' % file_name
            output = json.dumps(event, indent=4, sort_keys=True)
            open(key_path, "w").write(output)
            data = open(key_path, 'rb')
            s3.Bucket(os.environ['s3_bucket']).put_object(Key=file_name,
                                                          Body=data)
            logger.info("EVENT: %s" % str(event))
            batch.put_item(Item=event)
    return True


def lambda_handler(event, context):
    """Run the script."""
    body = event.get('body', dict())
    events = body.get('events', list())
    source_ip = str(event.get('source_ip', ''))
    if len(events) == 0:
        return {'success': False, 'message': "No events sent in"}
    status = process_events(events, source_ip)
    msg = "Wrote {} events to the cloud".format(len(events))
    return {'success': True, 'message': msg}
