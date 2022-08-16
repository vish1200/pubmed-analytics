import re
import time
from functools import wraps
from urllib.parse import urlparse
import shutil
from .exceptions import CanNotChangeFileName
import io
import os
import zipfile
import boto3
import json


NIHGOV_BASE = "ncbi.nlm.nih.gov"
BUCKET_NAME = os.environ.get('BUCKET_NAME', 'pubmed')
s3 = boto3.client('s3')


def retry(ExceptionToCheck, tries=4, delay=3, backoff=2, logger=None):
    """
    Retry calling the decorated function using an exponential backoff.
    http://www.saltycrane.com/blog/2009/11/trying-out-retry-decorator-python/
    original from: http://wiki.python.org/moin/PythonDecoratorLibrary#Retry
    :param ExceptionToCheck: the exception to check. may be a tuple of
        exceptions to check
    :type ExceptionToCheck: Exception or tuple
    :param tries: number of times to try (not retry) before giving up
    :type tries: int
    :param delay: initial delay between retries in seconds
    :type delay: int
    :param backoff: backoff multiplier e.g. value of 2 will double the delay
        each retry
    :type backoff: int
    :param logger: logger to use. If None, print
    :type logger: logging.Logger instance
    """
    def deco_retry(f):

        @wraps(f)
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 1:
                try:
                    return f(*args, **kwargs)
                except ExceptionToCheck as e:
                    msg = "%s, Retrying in %d seconds..." % (str(e), mdelay)
                    if logger:
                        logger.warning(msg)
                    else:
                        print(msg)
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            return f(*args, **kwargs)

        return f_retry  # true decorator

    return deco_retry


def parse_urls(urls):
    urls = urls.replace("\n", "")

    if ',' in urls:
        return urls.split(',')
    return [urls]


def contains_nihgov(urls: list):
    for url in urls:
        if NIHGOV_BASE in url:
            return True
    return False


def get_nihgov_url(urls: list):
    for url in urls:
        if NIHGOV_BASE in url:
            return url


def is_downloadable(session, url):
    """
    Check if the url contains a downloadable resource
    """
    h = session.head(url, allow_redirects=True)
    header = h.headers
    content_type = header.get('content-type')
    if 'text' in content_type.lower():
        return False
    if 'html' in content_type.lower():
        return False
    return True


def get_filename_from_cd(cd):
    """
    Get filename from content-disposition
    """
    if not cd:
        return None
    fname = re.findall('filename=(.+)', cd)
    if len(fname) == 0:
        return None
    return fname[0].strip("\"")


def get_unique_id_from_url(url):
    """
    :param url:
    :return: str
    """
    unique_id = urlparse(url).path.strip("/")
    return unique_id


def rename_file(old_file_name, new_file_name):
    try:
        shutil.move(old_file_name, new_file_name)
    except Exception:
        raise CanNotChangeFileName


def zip_file_objects(pdf_objects):
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zipper:
        for obj in pdf_objects:
            if obj['filename'].endswith('.pdf'):
                file_name = obj['filename'].split('/')[-1]
                obj = obj['obj']
                obj.seek(0)
                zipper.writestr(file_name, obj.read())

    return zip_buffer


def upload_to_s3(file_obj, key):
    """
        Upload file to S3 bucket and make it public
    """
    print(f"Uploading file to s3, key is {key}", time.ctime())
    if type(file_obj) == str:
        s3.put_object(Bucket=BUCKET_NAME, Key=key, Body=file_obj.encode('utf-8'), ACL='public-read')
    else:
        file_obj.seek(0)
        s3.put_object(Bucket=BUCKET_NAME, Key=key, Body=file_obj.read(), ACL='public-read')
    print(f"Finished uploading file to s3, key is {key}", time.ctime())


def readJSONFromS3(job_id):
    json_body = None
    s3_resource = boto3.resource('s3')
    bucket = s3_resource.Bucket(BUCKET_NAME)
    prefix_objs = bucket.objects.filter(Prefix=f"jobs/{job_id}/")
    for obj in prefix_objs:
        if obj.key.endswith('.json'):
            json_body = obj.get()['Body'].read().decode('utf-8')

    return json.loads(json_body)['data']


def split_JSONdata(data, count=4):
    """
        Split list into multi lists
        """
    row_count = len(data)
    interval = row_count//count
    frames = []

    if interval < 1:
        if len(data) and 'no' not in data[0]:
            no = 0
            for ind in range(len(data)):
                data[ind]['no'] = no
                no += 1
        return [data]

    for i in range(count):
        start = i * interval
        end = (i + 1) * interval
        if i == count - 1:
            end = row_count
        dt = data[start:end]
        if 'no' not in dt[0]:
            for ind in range(len(dt)):
                dt[ind]['no'] = start
                start += 1
        frames.append(dt)

    return frames

