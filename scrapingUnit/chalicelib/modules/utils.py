import os
import csv
from pandas.io.excel import ExcelWriter
import pandas
import io
import boto3
from threading import Thread
import multiprocessing


BUCKET_NAME = os.environ.get('BUCKET_NAME', 'pubmed')
s3 = boto3.client('s3')


def get_from_s3(key):
    obj = s3.get_object(Bucket=BUCKET_NAME, Key=key)
    return obj['Body'].read()


def upload_to_s3(file_obj, key):
    """
        Upload file to S3 bucket and make it public
    """
    if type(file_obj) == str:
        s3.put_object(Bucket=BUCKET_NAME, Key=key, Body=file_obj.encode('utf-8'), ACL='public-read')
    else:
        file_obj.seek(0)
        s3.put_object(Bucket=BUCKET_NAME, Key=key, Body=file_obj.read(), ACL='public-read')


def write_csv(csvdata):
    """
    Write lines to csv named as file object,
    """
    output_obj = io.StringIO()
    writer = csv.writer(output_obj, delimiter=',')
    writer.writerows(csvdata)

    # output_obj.seek(0)
    # with open('out.csv', mode='w') as f:
    #     f.write(output_obj.read())

    return output_obj


def excel_out(csv_file_obj):
    """
        Write CSV file object to excel object

        @params:
            csv_file_obj: ByteIO object
        """
    output_file_memory_obj = io.BytesIO()
    csv_file_obj.seek(0)
    # convert csv file to excel format
    with ExcelWriter(output_file_memory_obj) as ew:
        df = pandas.read_csv(csv_file_obj)
        df.to_excel(ew, sheet_name="sheet1", index=False)

    # output_file_memory_obj.seek(0)
    # with open('out.xlsx', mode='wb') as f:
    #     f.write(output_file_memory_obj.read())

    return output_file_memory_obj


def get_thread_range(thread_count, total_count):
    """
    Divide total units into array of threads
    @return: array
    """
    ranges = []
    interval = total_count//thread_count

    if interval > 1:
        for i in range(thread_count):
            ranges.append([x for x in range(interval * i, interval * (i + 1))])
        for x in range(thread_count * interval, total_count):
            ranges[thread_count - 1].append(x)
    else:
        return [x for x in range(total_count)]

    return ranges


def get_thread_page_range(thread_count, total_count):
    """
    Divide total units into array of threads
    @return: array
    """
    ranges = []
    for i in range(thread_count):
        ranges.append([])
    count = 0
    while count < total_count:
        for i in range(thread_count):
            count += 1
            ranges[i].append(count-1)
            if count == total_count:
                break

    return ranges


def get_thread_range_pumbed(process_count, total_count):
    """
    Divide total units into array of threads
    @return: array
    """
    ranges = []
    for i in range(process_count):
        ranges.append([])
    count = 1
    while count < total_count:
        for i in range(process_count):
            count += 1
            ranges[i].append(count)
            if count == total_count:
                break

    return ranges


def get_process_range_clinical(thread_count, total_count):
    _range = []
    end_number = total_count//100
    if total_count % 100 != 0:
        end_number += 1
    interval = end_number // thread_count + 1
    for i in range(thread_count):
        if (i+1)*interval > end_number:
            if end_number > i*interval:
                _range.append([i*interval, end_number+1])
            break
        thread_range = [i*interval, (i+1)*interval]
        _range.append(thread_range)
    return _range


def get_core_count():
    return multiprocessing.cpu_count()


class ThreadWithReturnValue(Thread):
    def __init__(self, group=None, target=None, name=None, args=(), kwargs={}, Verbose=None):
        Thread.__init__(self, group, target, name, args, kwargs)
        self._return = None

    def run(self):
        if self._target is not None:
            self._return = self._target(*self._args, **self._kwargs)

    def join(self, *args):
        Thread.join(self, *args)
        return self._return