from urllib.request import Request, urlopen, URLError
from urllib.parse import urljoin, urlparse, urlsplit, quote
from bs4 import BeautifulSoup
from igraph import *
import queue
import ssl
import re
from django.utils.encoding import iri_to_uri
import matplotlib.pyplot as plt


class Crawler():
    def __init__(self, base_url, max_depth, graph : Graph):

        self.graph = graph

        # znaki nie-ascii w url
        if not len(base_url) == len(base_url.encode()):
            base_url = iri_to_uri(base_url)

        self.graph.add_vertex(base_url, color='blue', label=base_url)

        self.links_to_crawl = queue.Queue()
        self.links_to_crawl.put(base_url)

        self.marked_pages = {}
        self.marked_pages[base_url] = 0

        self.max_depth = max_depth

        self.my_ssl = ssl.create_default_context()

        # by default when creating a default ssl context and making an handshake
        # we verify the hostname with the certificate but our objective is to crawl
        # the webpage so we will not be checking the validity of the cerfificate.
        self.my_ssl.check_hostname = False

        # in this case we are not verifying the certificate and any 
        # certificate is accepted in this mode.
        self.my_ssl.verify_mode = ssl.CERT_NONE

    def run(self):

        while True:

            print(f"Queue Size: {self.links_to_crawl.qsize()}")

            try:
                link = self.links_to_crawl.get_nowait()
            except:
                link = None

            if link is None:
                print(f"Total Number of pages visited are {len(self.marked_pages)}")
                return

            try:
                req = Request(link, headers= {'User-Agent': 'Mozilla/5.0'})
                response = urlopen(req, context = self.my_ssl)


                soup = BeautifulSoup(response.read(),"html.parser")

                for a_tag in soup.find_all('a'):
                    child_link = a_tag.get("href")

                    child_link = urljoin(link,child_link)

                    child_link_marked = child_link in self.marked_pages

                    if child_link_marked:
                        # sprawdzenie czy aktualne dojście do strony jest szybsze niż zapisane - jeżeli tak to trzeba ją jeszcze raz sprawdzić ze zmienioną wagą depth
                        current_depth = self.marked_pages[link]
                        current_child_depth = self.marked_pages[child_link]
                        child_depth = min(current_depth + 1, current_child_depth)

                        if child_depth < current_child_depth:
                            child_needs_revisit = True
                        else:
                            child_needs_revisit = False
                    else:
                        self.graph.add_vertex(child_link, label=child_link)
                        child_depth = self.marked_pages[link] + 1

                    # dodaj krawędź tylko jeżeli jej jeszcze nie ma
                    if not (self.graph.vs.find(name=child_link) in self.graph.vs.find(name=link).neighbors()):
                        self.graph.add_edge(link, child_link)

                    if ((not child_link_marked) and child_depth <= self.max_depth) or (child_link_marked and child_needs_revisit):
                        self.links_to_crawl.put(child_link)

                        if not len(child_link) == len(child_link.encode()):
                            child_link = iri_to_uri(child_link)
                        self.marked_pages[child_link] = child_depth

                print(f"{link} done")

            except URLError as e:
                print(f"ERROR {link} - {e.reason}")
            finally:
                self.links_to_crawl.task_done()

if __name__ == '__main__':

    print("The crawler is started")

    base_url = input("Please enter website to crawl > ")
    max_depth = int(input("Please enter max depth > "))

    graph = Graph()
    crawler = Crawler(base_url = base_url,
                      max_depth = max_depth,
                      graph = graph)

    crawler.run()

    # fig, ax = plt.subplots()

    # plot(graph, target=ax)

    # plt.show()

    plot(graph)
