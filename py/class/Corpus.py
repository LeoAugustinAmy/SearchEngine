import praw
import arxiv
import urllib
import xmltodict
import pandas as pd
from Document import Document
import datetime
from Author import Author

class Corpus :

    def __init__(self, subject, file_path = None) :
        """
        """
        self.subject = subject
        if (file_path) :
            self.docs = self.__getdocsWithCSV(file_path) # A reparer suite au changement de SDD
        else :
            self.docs, self.authors, self.nb_docs = self.__getDocsWithSubject(self.subject)


    def __getDocsWithSubject(self, subject: str) :
        """
        INFO :
            Générer une liste de liste qui contient à l'index 0 les document de reddit et à l'index 1 les documents de Arxiv
        INPUT :
            subject (str) --> le sujet rechercher par l'API
        OUTPUT :
            (tab) --> le tableau qui contient les documents des 2 appels API
        """

        authors = {}
        documents = {}
        id = 0

        # reddit
        redditConnection = praw.Reddit(client_id='3nZXcVfR162w5Yrcu6WkDQ', client_secret='Zyc2pI0jCgW4Cx6v4RTznsouqvXU7A', user_agent='SearchEngine')

        hotPosts = redditConnection.subreddit(subject).hot(limit=100)
        for post in hotPosts:
            text = post.selftext.replace('\n', ' ')
            if text:
                author_name = post.author.name if post.author else "Inconnu"
                print(author_name)
                doc = Document(post.title, author_name, post.created_utc, post.url, text)
                if (author_name != "Inconnu") and not(author_name in authors) :
                    authors[author_name] = Author(author_name)
                documents[id] = doc
                id += 1

        # Arxiv
        arxivDoc = []
        url = f'http://export.arxiv.org/api/query?search_query=all:{subject}&start=0&max_results=300'
        urlRead = urllib.request.urlopen(url).read()
        data = urlRead.decode()

        parsedData = xmltodict.parse(data)

        for entry in parsedData['feed']['entry'] :
            authors_list = entry.get('author', {})
            if isinstance(authors_list, list):
                for i in authors_list :
                    if not(i['name'] in authors) :
                        authors[i['name']] = Author(i['name'])
            else :
                if not(authors_list['name'] in authors) :
                    authors[authors_list['name']] = Author(authors_list['name'])

            doc = Document(entry['title'],authors_list, entry.get('published'), entry.get('id'), entry['summary'].replace('\n', ' '))
            documents[id] = doc
            id += 1

        return (documents, authors, len(documents))
    
    def __getdocsWithCSV(self, file_path) :
        df = pd.read_csv(file_path)
        print(f"Fichier chargé avec succès : {len(df)} lignes")

        return df

    def getDocs(self) :
        return self.docs

    def saveDocsCSV(self, folder: str) :
        df = self.DocstoDataframe()
        df.to_csv(folder + f"/{self.subject}.csv", index=False)

    def getNbDocs(self) :
        return self.nb_docs
    
    def seeNbWordsDocs(self) :
        df = self.DocstoDataframe()
        for i in df['Texte'] :
            print(len(i.split(" ")))

    def clearDocsByNumberOfWords(self, nbWordsMin: int):
        df = self.DocstoDataframe()
        df = df[df['Texte'].apply(lambda x: len(x.split()) >= nbWordsMin)]
        return self.docs
    
    def showDocs(self, limit = -1) :
        if (limit == -1) :
            for i in self.docs :
                print(i)
        else :
            nb = 0
            while nb < limit :
                print(self.docs[i])

    def DocstoDataframe(self) :
        df = pd.DataFrame(
        [vars(doc) for doc in self.docs.values()],  # récupère tous les attributs des objets
        index=self.docs.keys()                      # garde les ID comme index
         )

        return df


    
Corpus = Corpus("Quantum")
print(Corpus.DocstoDataframe().tail)
Corpus.saveDocsCSV("C:/Users/leoam/Desktop/M1/programmation de spécialité/SearchEngine/py/output")

# TODO : TD4, 3.2

