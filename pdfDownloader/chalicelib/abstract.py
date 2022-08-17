from abc import ABC, abstractmethod


class Site(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def get_page_source(self):
        pass

    @abstractmethod
    def get_pdf_url(self, **args):
        pass

    @abstractmethod
    def download_pdf(self, **args):
        pass
    
    @abstractmethod
    def start_scrape(self):
        pass
