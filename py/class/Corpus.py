import praw
import arxiv
import urllib
import xmltodict
import pandas as pd
from Document import *
import datetime
import json
from Author import Author
import re

class Corpus :
    def __init__(self, subject, file_path=None):
        """
        Initialise le corpus. Charge depuis un JSON si file_path est fourni,
        sinon interroge les API.
        """
        self.subject = subject
        self.authors = {}
        self.docs = {}
        if file_path:
            self.load_json(file_path)
        else:
            self.docs, self.authors, self.nb_docs = self.__getDocsWithSubject(self.subject)
        self.last_id = 0
        self.textOnOneLine = self.getOneLineOfText()


    def __getDocsWithSubject(self, subject: str) :
        """
        Générer une liste de liste qui contient à l'index 0 les document de reddit et à l'index 1 les documents de Arxiv.
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

            doc = ArxivDocument(entry['title'],auteur_principal, entry.get('published'), entry.get('id'), entry['summary'].replace('\n', ' '), co_auteur)
            documents[id] = doc
            id += 1

        return (documents, authors, len(documents))

    def save_json(self, file_path):
        """
        Sauvegarde le dictionnaire de documents au format JSON.
        INPUT :
            file_path (str)
        """
        # On transforme chaque objet Document en dictionnaire pour le rendre sérialisable
        data_to_save = {}

        for i, doc in self.docs.items():
            # On récupère les attributs de l'objet Document
            doc_dict = vars(doc).copy()

            # Simple auteur
            if hasattr(doc.auteur, 'name'):
                doc_dict['auteur'] = doc.auteur.name
            data_to_save[str(i)] = doc_dict

            # Co auteur
            if 'co_auteur' in doc_dict and isinstance(doc_dict['co_auteur'], list):
                # On remplace chaque objet Author de la liste par son nom
                doc_dict['co_auteur'] = [
                    a.name if hasattr(a, 'name') else str(a) 
                    for a in doc_dict['co_auteur']
                ]

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, ensure_ascii=False, indent=4)
        print(f"Corpus sauvegardé en JSON : {file_path}")

    def load_json(self, file_path):
        """
        Charge un corpus depuis un JSON où les documents sont à la racine.
        INPUT :
            file_path (str)
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.docs = {}
            self.authors = {}

            # On boucle directement sur les clés du dictionnaire chargé
            for idx, d in data.items():
                # On ignore les éventuelles méta-données comme 'subject'
                if not idx.isdigit() and idx == "subject":
                    self.subject = d
                    continue

                # 1. Reconstruction de l'Auteur
                author_name = d.get('auteur', 'Inconnu')
                if author_name not in self.authors:
                    self.authors[author_name] = Author(author_name)
                author_obj = self.authors[author_name]

                # 2. Reconstruction du Document selon le type
                doc_type = d.get('type')

                if doc_type == "Reddit":
                    new_doc = RedditDocument(
                        titre=d.get('titre'),
                        auteur=author_name,
                        date=d.get('date'),
                        url=d.get('url'),
                        texte=d.get('texte'),
                        nb_comment=d.get('nb_comment', 0)
                    )
                elif doc_type == "Arxiv":
                    new_doc = ArxivDocument(
                        titre=d.get('titre'),
                        auteur=author_name,
                        date=d.get('date'),
                        url=d.get('url'),
                        texte=d.get('texte'),
                        co_auteur=d.get('co_auteur', [])
                    )
                else:
                    new_doc = Document(
                        titre=d.get('titre'),
                        auteur=author_name,
                        date=d.get('date'),
                        url=d.get('url'),
                        texte=d.get('texte')
                    )

                # 3. Stockage et liaison avec l'auteur
                self.docs[int(idx)] = new_doc
                author_obj.add(new_doc)

            self.nb_docs = len(self.docs)
            print(f"Chargement réussi : {self.nb_docs} documents chargés.")

        except FileNotFoundError:
            print("Erreur : Le fichier est introuvable.")

    def getDocs(self) :
        return self.docs

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
        """
        INFO :
            Genère un seul string à partir de tout les textes récupérer depuis l'API
        INPUT :
            self (Corpus) --> Objet qui contient tout les documents
        OUTPUT :
            (str) --> Une chaine de caractère qui contient un join de tout les textes
        """
        textes = [doc.texte for doc in self.docs.values()]
        return "".join(textes)

# ===================== From here, function for TD 2 =====================

    def search(self, find) :
        """
        INFO :
            recherche dans une chaine de caractere un motif en particulier
        INPUT :
            self (Corpus) --> Objet qui contient tout les documents
            find (str) --> chainde de caractere à rechercher
        OUTPUT :
            (tab) --> un tableau qui contient tout les passages ou apparait find
        """
        phrases = re.split(r'(?<=[.!?])\s+', self.textOnOneLine)

        pattern = rf"\b{re.escape(find)}\b"

        results = [p for p in phrases if re.search(pattern, p, flags=re.IGNORECASE)]

        return results

    def concorde(self, find, contexte=30):
        """
        INFO :
            Construit un concordancier : contexte gauche, motif trouvé, contexte droit.
        INPUT :
            self (Corpus) --> Objet qui contient tout les documents
            find (str) --> chainde de caractere à rechercher
            contexte (int) --> le nombre de caractere à prendre autour du str find
        OUTPUT :
            (DataFrame) --> un dtaaframe pandas avec 3 colonnes
        """
        pattern = rf"(.{{0,{contexte}}})\b({re.escape(find)})\b(.{{0,{contexte}}})"

        matches = re.findall(pattern, self.textOnOneLine, flags=re.IGNORECASE)

        df = pd.DataFrame(matches, columns=["contexte_gauche", "motif", "contexte_droit"])
        return df

    def nettoyer_texte(self, texte):
        """
        INFO :
            Nettoie un texte : minuscules, supprime ponctuation, chiffres, sauts de ligne.
        INPUT :
            self (Corpus) --> Objet qui contient tout les documents
            texte (str) --> Le texte à nettoyer
        OUTPUT :
            (DataFrame) --> Un dtaaframe pandas avec 3 colonnes
        """
        texte = texte.lower()
        texte = texte.replace("\n", " ")
        texte = re.sub(r"[^\w\s]", " ", texte)  # retire la ponctuation
        texte = re.sub(r"\d+", " ", texte)       # retire les chiffres
        texte = re.sub(r"\s+", " ", texte)       # espaces multiples --> un seul
        return texte.strip()

    def construire_vocabulaire(self):
        """
        INFO :
            Construit le vocabulaire (ensemble des mots uniques du corpus)
        INPUT :
            self (Corpus) --> Objet qui contient tout les documents
        OUTPUT :
            (Set) --> X
        """
        vocab = set()

        for doc in self.docs.values():
            propre = self.nettoyer_texte(doc.texte)
            mots = propre.split()
            vocab.update(mots)

        return vocab

    def stats(self, n=20):
        """
        INFO :
            Affiche en console des statistiques clefs
        INPUT :
            self (Corpus) --> Objet qui contient tout les documents
            n (int) --> Sert à l'affichage uniquement, affiche les n mots les plus presents
        """

        vocab = {}
        doc_freq = {}

        for doc in self.docs.values():
            propre = self.nettoyer_texte(doc.texte)
            mots = propre.split()

            mots_uniques_doc = set(mots)

            for m in mots:
                vocab[m] = vocab.get(m, 0) + 1

            for m in mots_uniques_doc:
                doc_freq[m] = doc_freq.get(m, 0) + 1

        df = pd.DataFrame({
            "mot": list(vocab.keys()),
            "term_frequency": list(vocab.values()),
            "document_frequency": [doc_freq[m] for m in vocab.keys()]
        })

        df = df.sort_values(by="term_frequency", ascending=False)

        print("Nombre de mots différents :", len(df))
        print(f"\nTop {n} mots les plus fréquents :")
        print(df.head(n))

        return df

    def sort_by_date(self, n=10):
        """
        Affiche les n documents les plus récents.
        """
        # On force la comparaison en texte pour éviter l'erreur float/str
        sorted_docs = sorted(self.docs.values(), key=lambda x: str(x.date), reverse=True)
        for doc in sorted_docs[:n]:
            print(doc)

    def sort_by_title(self, n=10):
        """
        Affiche les n premiers documents triés par titre.
        """
        sorted_docs = sorted(self.docs.values(), key=lambda x: x.titre)
        for doc in sorted_docs[:n]:
            print(doc)

    def __repr__(self):
        """
        Fournit une représentation du corpus.
        OUTPUT : (str)
        """
        return f"Corpus(sujet='{self.subject}', nb_documents={len(self.docs)}, nb_auteurs={len(self.authors)})"


my_corpus = Corpus("Quantum")
print(f"Représentation du corpus : {my_corpus}")
