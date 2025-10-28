import praw
import arxiv
import urllib
import xmltodict
from pandas import *

class API :

    def __init__(self, subject) :
        """
        """
        self.subject = subject
        self.docs = self.__getDocsWithSubject(self.subject)


    def __getDocsWithSubject(self, subject) :
        """
        INFO :
            Générer une liste de liste qui contient à l'index 0 les document de reddit et à l'index 1 les documents de Arxiv
        INPUT :
            subject (str) --> le sujet rechercher par l'API
        OUTPUT :
            (tab) --> le tableau qui contient les documents des 2 appels API
        """
        # praw --> the docs from reddit are in index 0 of the final tab
        redditDocs = []
        redditConnection = praw.Reddit(client_id='3nZXcVfR162w5Yrcu6WkDQ', client_secret='Zyc2pI0jCgW4Cx6v4RTznsouqvXU7A', user_agent='SearchEngine')

        hotPosts = redditConnection.subreddit(subject).hot(limit=100)
        for post in hotPosts:
            text = post.selftext.replace('\n', ' ')
            if text:
                redditDocs.append(text)

        # Arxiv --> the docs from Arxiv are in index 1 of the final tab
        arxivDoc = []
        url = f'http://export.arxiv.org/api/query?search_query=all:{subject}&start=0&max_results=300'
        urlRead = urllib.request.urlopen(url).read()
        data = urlRead.decode()

        parsedData = xmltodict.parse(data)

        for entry in parsedData['feed']['entry']:
            summary = entry['summary'].replace('\n', ' ')
            arxivDoc.append(summary)

        return [redditDocs, arxivDoc]
    
    def getDocs(self) :
        return self.docs
    
API = API("Quantum")
print(API.getDocs())
