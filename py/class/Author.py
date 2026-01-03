class Author :
    def __init__(self, name):
        """
        Initialise un auteur.
        INPUT :
            name (str)
        """
        self.name = name
        self.production = {}
        self.nb_docs = 0

    def add(self, document):
        """
        Ajoute un document à la production de l'auteur.
        INPUT : document (objet Document)
        """
        self.production[len(self.production) + 1] = document
        self.nb_docs = len(self.production)

    def get_stats(self):
        """
        Calcule des statistiques pour l'auteur : nombre de docs et taille moyenne.
        OUTPUT :
            (int, float)
        """
        total_chars = sum(len(doc.texte) for doc in self.production.values())
        avg_size = total_chars / self.nb_docs if self.nb_docs > 0 else 0
        return self.nb_docs, avg_size

    def __str__(self):
        """
        Version lisible de l'objet Author.
        """
        return f"Auteur : {self.name} | Documents publiés : {self.nb_docs}"