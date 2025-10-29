class Document:
    def __init__(self, titre, auteur, date, url, texte):
        self.titre = titre
        self.auteur = auteur
        self.date = date
        self.url = url
        self.texte = texte

    def __showAttribute(self):
        print(f"Titre : {self.titre}")
        print(f"Auteur : {self.auteur}")
        print(f"Date : {self.date}")
        print(f"URL : {self.url}")
        print(f"Texte : {self.texte[:80]}...")  # affiche juste le début

    def __str__(self):
        return f"{self.titre} | {self.auteur} | {self.date}"


class RedditDocument(Document):
    def __init__(self, titre, auteur, date, url, texte, nb_comment):
        super().__init__(titre, auteur, date, url, texte)
        self.nb_comment = nb_comment

    def getNbComment(self):
        return self.nb_comment

    def setNbComment(self, nb_comment):
        self.nb_comment = nb_comment

    def __str__(self):
        return f"{super().__str__()} | commentaires : {self.nb_comment}"


class ArxivDocument(Document):
    def __init__(self, titre, auteur, date, url, texte, co_auteur):
        super().__init__(titre, auteur, date, url, texte)
        self.co_auteur = co_auteur

    def getCoAuteur(self):
        return self.co_auteur

    def setCoAuteur(self, co_auteur):
        self.co_auteur = co_auteur

    def __str__(self):
        return f"{super().__str__()} | co-auteurs : {self.co_auteur}"
