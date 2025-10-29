class Author :
    def __init__(self, name):
        self.name = name
        self.production = {}
        self.nb_docs = len(self.production)

    def add(self, document) :
        self.production[self.nb_docs + 1] = document
        self.nb_docs += 1

    def __str__(self):
        return f"Auteur : {self.name} | production : {self.production}"

    def getNbDocs(self) :
        return self.nb_docs