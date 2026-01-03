class Document:
    def __init__(self, titre, auteur, date, url, texte, type_doc="Inconnu"):
        """
        Initialise un document générique.
        INPUT :
            titre (str), auteur (str), date (str/datetime), url (str), texte (str), type_doc (str)
        """
        self.titre = titre
        self.auteur = auteur
        self.date = str(date)
        self.url = url
        self.texte = texte
        self.type = type_doc

    def __str__(self):
        """
        Affiche une version texte de l'instance.
        OUTPUT :
            (str)
        """
        return f"[{self.type}] {self.titre} | {self.auteur} | {self.date}"

class RedditDocument(Document):
    def __init__(self, titre, auteur, date, url, texte, nb_comment):
        """
        Initialise un document provenant de Reddit.
        INPUT :
            idem Document + nb_comment (int)
        """
        super().__init__(titre, auteur, date, url, texte, type_doc="Reddit")
        self.nb_comment = nb_comment

    def getType(self):
        """
        Retourne le type de la source.
        """
        return "Reddit"

    def __str__(self):
        return f"{super().__str__()} | commentaires : {self.nb_comment}"

class ArxivDocument(Document):
    def __init__(self, titre, auteur, date, url, texte, co_auteur):
        """
        Initialise un document provenant d'Arxiv.
        INPUT :
            idem Document + co_auteur (list)
        """
        super().__init__(titre, auteur, date, url, texte, type_doc="Arxiv")
        self.co_auteur = co_auteur

    def getType(self):
        """
        Retourne le type de la source.
        """
        return "Arxiv"

    def __str__(self):
        return f"{super().__str__()} | co-auteurs : {self.co_auteur}"