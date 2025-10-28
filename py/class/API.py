import praw
import arxiv
import urllib
import xmltodict
import pandas as pd
from Document import Document
import datetime

class API :

    def __init__(self, subject, file_path = None) :
        """
        """
        self.subject = subject
        if (file_path) :
            self.docs = self.__getdocsWithCSV(file_path)
        else :
            self.docs = self.__getDocsWithSubject(self.subject)


    def __getDocsWithSubject(self, subject: str) :
        """
        INFO :
            Générer une liste de liste qui contient à l'index 0 les document de reddit et à l'index 1 les documents de Arxiv
        INPUT :
            subject (str) --> le sujet rechercher par l'API
        OUTPUT :
            (tab) --> le tableau qui contient les documents des 2 appels API
        """

        documents = {}
        id = 0

        # reddit
        redditConnection = praw.Reddit(client_id='3nZXcVfR162w5Yrcu6WkDQ', client_secret='Zyc2pI0jCgW4Cx6v4RTznsouqvXU7A', user_agent='SearchEngine')

        hotPosts = redditConnection.subreddit(subject).hot(limit=100)
        for post in hotPosts:
            text = post.selftext.replace('\n', ' ')
            if text:
                doc = Document(post.title, [post.author.name] if post.author else "Inconnu", post.created_utc, post.url, text)
                documents[id] = doc
                id += 1

        # Arxiv
        arxivDoc = []
        url = f'http://export.arxiv.org/api/query?search_query=all:{subject}&start=0&max_results=300'
        urlRead = urllib.request.urlopen(url).read()
        data = urlRead.decode()

        parsedData = xmltodict.parse(data)

        for entry in parsedData['feed']['entry'] :
            doc = Document(entry['title'], entry.get('author', {}), entry.get('published'), entry.get('id'), entry['summary'].replace('\n', ' '))
            documents[id] = doc
            id += 1

        return documents
    
    def __getdocsWithCSV(self, file_path) :
        df = pd.read_csv(file_path)
        print(f"Fichier chargé avec succès : {len(df)} lignes")

        return df

    def getDocs(self) :
        return self.docs

    def saveDocsCSV(self, folder: str) :
        self.docs.to_csv(folder + f"/{self.subject}.csv", index=False)

    def getNbDocs(self) :
        return len(self.docs)
    
    def seeNbWordsDocs(self) :
        for i in self.docs['Texte'] :
            print(len(i.split(" ")))

    def clearDocsByNumberOfWords(self, nbWordsMin: int):
        self.docs = self.docs[self.docs['Texte'].apply(lambda x: len(x.split()) >= nbWordsMin)]
        return self.docs


    
API = API("Quantum")
print(API.getDocs())
