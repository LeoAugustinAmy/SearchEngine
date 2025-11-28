import praw
import arxiv
import urllib
import xmltodict
import pandas as pd
from Document import *
import datetime
from Author import Author
import re

class Corpus :

    def __init__(self, subject, file_path = None) :
        """
        """
        self.subject = subject
        if (file_path) :
            self.docs = self.__getdocsWithCSV(file_path) # A reparer suite au changement de SDD
        else :
            self.docs, self.authors, self.nb_docs = self.__getDocsWithSubject(self.subject)
        self.last_id = 0


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
                doc = RedditDocument(post.title, author_name, post.created_utc, post.url, text, post.num_comments)
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
            auteur_principal = None
            co_auteur = []
            if isinstance(authors_list, list):
                first_time = True
                for i in authors_list :
                    if not(i['name'] in authors) :
                        authors[i['name']] = Author(i['name'])
                    if not(first_time) :
                        co_auteur.append(Author(i['name']))
                    first_time = False

            else :
                auteur_principal = Author(authors_list['name'])
                if not(authors_list['name'] in authors) :
                    authors[authors_list['name']] = auteur_principal

            if co_auteur == [] :
                co_auteur = "Aucun co-auteur(s)"

            print(co_auteur)
            doc = ArxivDocument(entry['title'],auteur_principal, entry.get('published'), entry.get('id'), entry['summary'].replace('\n', ' '), co_auteur)
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

# ===================== From here, function to add to TD 1 =====================

    def getOneLineOfText(self) :
        textes = [doc.texte for doc in self.docs.values()]
        return "".join(textes)

# ===================== From here, function for TD 2 =====================

corpus = Corpus("Quantum")
print(corpus.getOneLineOfText())
