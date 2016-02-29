from __future__ import print_function

import sys
import boto3
import json
import logging
import hashlib
import hmac
import base64
import urllib
import urllib2
from urlparse import urlparse
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

logger.info("Version 0.0.1")

def lambda_handler(event, context):
    return request(event['endpoint'], event['params'], settings(event['bucketName']))

def request(endpoint, params, settings):
    logger.info("Request to %s: %s" % (endpoint, str(params)))

    params['Service'] = 'AWSECommerceService'
    params['Version'] = '2013-08-01'
    params['AWSAccessKeyId'] = settings['AWSAccessKeyId']
    params['AssociateTag'] = settings['AssociateTag']
    params['Timestamp'] = datetime.utcnow().isoformat()

    query = urllib.urlencode(params)
    sig = signature(settings['AWSSecretKey'], endpoint, query)
    url = "%s?%s&Signature=%s" % (endpoint, query, sig)

    logger.info("Request: " + url)
    try:
        res = urllib2.urlopen(url)
        return res.read()
    except urllib2.HTTPError as ex:
        logger.info("Error: " + ex)
        return '<error code="%s" reason="%s" />' % (ex.code, ex.reason)

def signature(secret, endpoint, query):
    string = '&'.join(sorted(query.split('&')))
    url = urlparse(endpoint)
    tosign = '\n'.join(['GET', url.netloc, url.path, string])
    logger.info("Signing: " + tosign)

    digest = hmac.new(key=secret.encode(), msg=tosign, digestmod=hashlib.sha256).digest()
    return urllib.quote_plus(base64.b64encode(digest))

def settings(bucketName):
    s3 = boto3.resource('s3')
    file = s3.Object(bucketName, 'lambda/settings.json')
    data = file.get()['Body']
    return json.load(data)['amazon']

if __name__ == "__main__":
    logging.basicConfig()

    endpoint = sys.argv[1]
    bucketName = sys.argv[2]
    filename = sys.argv[3]

    params = json.load(open(filename, 'r'))
    res = request(endpoint, params, settings(bucketName))
    print(res)
