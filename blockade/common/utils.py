"""Common utilities shared across all libraries."""


def clean_indicators(indicators):
    """Remove any extra details from indicators."""
    output = list()
    for indicator in indicators:
        strip = ['http://', 'https://']
        for item in strip:
            indicator = indicator.replace(item, '')
        indicator = indicator.strip('.').strip()
        parts = indicator.split('/')
        if len(parts) > 0:
            indicator = parts.pop(0)
        output.append(indicator)
    output = list(set(output))
    return output


def is_hashed(value):
    """Identify if a value appears hashed using regex."""
    import re
    return re.search(r"^([a-fA-F\d]{32})$", value)


def hash_values(values, alg="md5"):
    """Hash a list of values."""
    import hashlib
    if alg not in ['md5', 'sha1', 'sha256']:
        raise Exception("Invalid hashing algorithm!")

    hasher = getattr(hashlib, alg)
    if type(values) == str:
        output = hasher(values).hexdigest()
    elif type(values) == list:
        output = list()
        for item in values:
            output.append(hasher(item).hexdigest())
    return output


def check_whitelist(values):
    """Check the indicators against known whitelists."""
    import os
    import tldextract
    whitelisted = list()
    for name in ['alexa.txt', 'cisco.txt']:
        config_path = os.path.expanduser('~/.config/blockade')
        file_path = os.path.join(config_path, name)
        whitelisted += [x.strip() for x in open(file_path, 'r').readlines()]
    output = list()
    for item in values:
        ext = tldextract.extract(item)
        if ext.registered_domain in whitelisted:
            continue
        output.append(item)
    return output


def cache_items(values):
    """Cache indicators that were successfully sent to avoid dups."""
    import os
    config_path = os.path.expanduser('~/.config/blockade')
    file_path = os.path.join(config_path, 'cache.txt')
    if not os.path.isfile(file_path):
        file(file_path, 'w').close()
    written = [x.strip() for x in open(file_path, 'r').readlines()]
    handle = open(file_path, 'a')
    for item in values:
        # Because of the option to submit in clear or hashed, we need to make
        # sure we're not re-hashing before adding.
        if is_hashed(item):
            hashed = item
        else:
            hashed = hash_values(item)

        if hashed in written:
            continue
        handle.write(hashed + "\n")
    handle.close()
    return True


def prune_cached(values):
    """Remove the items that have already been cached."""
    import os
    config_path = os.path.expanduser('~/.config/blockade')
    file_path = os.path.join(config_path, 'cache.txt')
    if not os.path.isfile(file_path):
        return values
    cached = [x.strip() for x in open(file_path, 'r').readlines()]
    output = list()
    for item in values:
        hashed = hash_values(item)
        if hashed in cached:
            continue
        output.append(item)
    return output


def get_logger(name):
    """Get a logging instance we can use."""
    import logging
    import sys
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    shandler = logging.StreamHandler(sys.stdout)
    fmt = ""
    fmt += '\033[1;32m%(levelname)-5s %(module)s:%(funcName)s():'
    fmt += '%(lineno)d %(asctime)s\033[0m| %(message)s'
    fmtr = logging.Formatter(fmt)
    shandler.setFormatter(fmtr)
    logger.addHandler(shandler)
    return logger


def process_whitelists():
    """Download approved top 1M lists."""
    import csv
    import grequests
    import os
    import StringIO
    import zipfile
    mapping = {
        'http://s3.amazonaws.com/alexa-static/top-1m.csv.zip': {
            'name': 'alexa.txt'
        }, 'http://s3-us-west-1.amazonaws.com/umbrella-static/top-1m.csv.zip': {
            'name': 'cisco.txt'
        }
    }
    rs = (grequests.get(u) for u in mapping.keys())
    responses = grequests.map(rs)
    for r in responses:
        data = zipfile.ZipFile(StringIO.StringIO(r.content)).read('top-1m.csv')
        stream = StringIO.StringIO(data)
        reader = csv.reader(stream, delimiter=',', quoting=csv.QUOTE_MINIMAL)
        items = [row[1].strip() for row in reader]
        stream.close()

        config_path = os.path.expanduser('~/.config/blockade')
        file_path = os.path.join(config_path, mapping[r.url]['name'])
        handle = open(file_path, 'w')
        for item in items:
            if item.count('.') == 0:
                continue
            handle.write(item + "\n")
        handle.close()
    return True
