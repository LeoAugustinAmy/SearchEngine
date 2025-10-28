class Document :

    def __init__(self, titre, auteur, date, url, texte):
        self.titre = titre
        self.auteur = auteur
        self.date = date
        self.url = url
        self.texte = texte

    def __showAttribute(self) :
        print(self.titre)
        print(self.auteur)
        print(self.date)
        print(self.url)
        print(self.texte)

    def __str__(self):
        print(self.titre)