from multiprocessing import Process, Manager
from datetime import datetime
import os
from threading import Thread
from .utils import process_unit, splitter, download_zip


def thread_job(zipObj, filenames):
    """
        Threading Unit to process unit files
        """
    text_data_arr = []
    for filename in filenames:
        text_data = process_unit(zipObj, filename)
        text_data_arr.append(text_data)

    return text_data_arr


class ThreadWithReturnValue(Thread):
    """
        Multi threading module
        """
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
        MultiProcessing module
        """
    def __init__(self, filenames, zipObj, results_dict):
        super(MultiProcess, self).__init__()
        self.filenames = filenames
        self.zipObj = zipObj
        self.results_dict = results_dict

    def run(self):
        print("Row count for this process:", len(self.filenames), datetime.now())
        thread_count = 5
        fnames = splitter(data=self.filenames, count=thread_count)

        threads = []
        for names in fnames:
            thread = ThreadWithReturnValue(target=thread_job, args=(self.zipObj, names,))
            thread.start()
            threads.append(thread)

        for thread in threads:
            text_data_arr = thread.join()

            print("Before", len(self.results_dict))
            self.results_dict += text_data_arr
            print("After", len(self.results_dict))


def Extract_Job(job_id):
    manager = Manager()
    results_dict = manager.list()

    zip_path = f"jobs/{job_id}/pdfs.zip"
    print(f"Reading Zip file from s3: {zip_path}", datetime.now())
    zipObj, file_list = download_zip(zip_path=zip_path)
    print(f"Readed Zip file, Total file count:", len(file_list), datetime.now())

    processes = []
    # Thread count
    process_count = 4
    fnames = splitter(data=file_list, count=process_count)

    print("Started extracting", datetime.now())
    for names in fnames:
        proc = MultiProcess(
            filenames=names,
            zipObj=zipObj,
            results_dict=results_dict
        )
        proc.start()
        processes.append(proc)

    for proc in processes:
        proc.join()
    print("Finished downloading", datetime.now())
    return results_dict
