from multiprocessing import Process, Manager
from datetime import datetime
import time
import os
from threading import Thread
from chalicelib.downloader import Downloader
from chalicelib.helpers import split_JSONdata, readJSONFromS3


def thread_job(unit):
    pdf_objects, data = unit.run()
    return pdf_objects, data


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


class MultiProcess(Process):
    """
        Threading module
        """
    def __init__(self, data, results_dict, results_pdfs, download_dir):
        super(MultiProcess, self).__init__()
        self.data = data
        self.results_dict = results_dict
        self.results_pdfs = results_pdfs
        self.download_dir = download_dir

    def run(self):
        print("Row count for this process:", len(self.data), datetime.now())
        thread_count = 5
        frames = split_JSONdata(data=self.data, count=thread_count)

        threads = []
        for frame in frames:
            if len(frame):
                unit = Downloader(data=frame, download_dir=self.download_dir)
                thread = ThreadWithReturnValue(target=thread_job, args=(unit,))
                thread.start()
                threads.append(thread)

        for thread in threads:
            pdf_objects, data = thread.join()

            print("Before", len(self.results_dict), len(self.results_pdfs))
            self.results_dict += data
            self.results_pdfs += pdf_objects
            print("After", len(self.results_dict), len(self.results_pdfs))


def Pdf_Job(job_id):
    manager = Manager()
    results_dict = manager.list()
    results_pdfs = manager.list()

    print("Reading JSON file from s3", datetime.now())
    json_data = readJSONFromS3(job_id=job_id)
    print(f"Readed JSON, Total Count:", len(json_data), datetime.now())

    ts = datetime.now().strftime('%Y-%m-%d-%H-%M_%S')
    download_dir = f"/tmp/downloads_{ts}"
    try:
        os.mkdir(download_dir)
    except Exception as e:
        print(e)

    processes = []
    # Thread count
    process_count = 4
    frames = split_JSONdata(data=json_data, count=process_count)

    print("Started downloading", datetime.now())
    for frame in frames:
        if frame:
            if len(frame):
                proc = MultiProcess(
                    data=frame,
                    results_dict=results_dict,
                    results_pdfs=results_pdfs,
                    download_dir=download_dir
                )
                proc.start()
                processes.append(proc)

    for proc in processes:
        proc.join()
    print("Finished downloading", datetime.now())
    return results_dict, results_pdfs

