import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
import math
from Corpus import Corpus


class SearchEngine :

    def __init__(self, corpus):
        """
        Initialise le moteur de recherche à partir d’un Corpus.
        Construit directement :
            - vocabulaire
            - matrice TF
            - statistiques (TF total, DF)
            - matrice TF-IDF
        """
        self.corpus = corpus
        self.docs = corpus.docs
        self.nb_docs = corpus.nb_docs

        self.vocab = self.__build_vocab()
        self.word2id = { mot : self.vocab[mot]["id"] for mot in self.vocab }
        self.id2word = { self.vocab[m]["id"] : m for m in self.vocab }

        self.mat_TF = self.__build_TF_matrix()
        self.__compute_vocab_stats()
        self.mat_TFIDF = self.__build_TFIDF_matrix()


    def __build_vocab(self):
        """
        ÉTAPE 1 : Construction de l'index lexical.
        On parcourt tout le corpus pour identifier chaque mot unique.
        On leur assigne un ID unique (index de colonne dans nos futures matrices)
        et on initialise les compteurs pour les stats globales (Fréquence totale et Document Frequency).
        """
        vocab = {}
        next_id = 0

        for d in self.docs.values():
            # Prétraitement : on utilise la méthode de nettoyage du corpus (minuscules, ponctuation...)
            propre = self.corpus.nettoyer_texte(d.texte)
            mots = propre.split()

            for m in mots:
                if m not in vocab:
                    vocab[m] = {
                        "id": next_id, # Position fixe dans le futur vecteur
                        "total_occ": 0,
                        "df": 0 # Nombre de documents contenant ce mot
                    }
                    next_id += 1
        return vocab

    def __build_TF_matrix(self):
        """
        ÉTAPE 2 : Construction de la matrice de fréquences (Term Frequency).
        On utilise une 'sparse matrix' (CSR) de Scipy car la majorité des cellules
        sont à zéro (un document ne contient qu'une fraction du vocabulaire total).
        C'est indispensable pour optimiser la mémoire vive (RAM).
        """
        rows, cols, data = [], [], []

        for doc_id, d in self.docs.items():
            propre = self.corpus.nettoyer_texte(d.texte)
            mots = propre.split()

            # On compte les occurrences locales dans le document courant
            compteur = {}
            for m in mots:
                if m in self.vocab:
                    compteur[m] = compteur.get(m, 0) + 1

            # On remplit les listes pour construire la matrice creuse
            for m, c in compteur.items():
                rows.append(doc_id) # Axe Y : Index du document
                cols.append(self.vocab[m]["id"]) # Axe X : Index du mot
                data.append(c) # Valeur : Nombre d'apparitions

        return csr_matrix((data, (rows, cols)), shape=(self.nb_docs, len(self.vocab)))

    def __compute_vocab_stats(self):
        """
        ÉTAPE 3 : Calcul des statistiques globales du vocabulaire.
        On extrait les colonnes de la matrice TF pour mettre à jour les infos du dictionnaire vocab.
        total_occ = somme de la colonne (fréquence globale).
        df = nombre d'éléments non nuls dans la colonne (popularité du mot dans le corpus).
        """
        for mot, info in self.vocab.items():
            j = info["id"]
            col = self.mat_TF[:, j] # Extraction de la colonne du mot j

            info["total_occ"] = int(col.sum())
            info["df"] = col.count_nonzero()

    def __build_TFIDF_matrix(self):
        """
        ÉTAPE 4 : Pondération TF-IDF.
        Le but est de réduire l'importance des mots trop fréquents (ex: 'le', 'et')
        et de valoriser les mots rares et discriminants pour la recherche.
        Formule utilisée : TF(i,j) * log(N / DF(j))
        """
        rows, cols, data = [], [], []
        N = self.nb_docs
        TF = self.mat_TF

        for i in range(N):
            row = TF.getrow(i) # Optimisation : on ne traite que les valeurs non nulles
            indices = row.indices
            values = row.data

            for j, tf in zip(indices, values):
                df = self.vocab[self.id2word[j]]["df"]
                if df > 0:
                    # Calcul de l'Inverse Document Frequency
                    idf = math.log(N / df)
                    val = tf * idf
                    rows.append(i)
                    cols.append(j)
                    data.append(val)

        return csr_matrix((data, (rows, cols)), shape=TF.shape)

    def __query_to_vector(self, mots):
        """
        ÉTAPE 5 : Vectorisation de la requête.
        On transforme la chaîne de caractères saisie par l'utilisateur en un
        vecteur de même dimension que nos documents pour pouvoir les comparer.
        On applique la même pondération TF-IDF que pour le corpus.
        """
        mots_nettoyes = self.corpus.nettoyer_texte(mots).split()
        vec = np.zeros(len(self.vocab))

        counts = {}
        for m in mots_nettoyes:
            if m in self.word2id:
                counts[m] = counts.get(m, 0) + 1

        for m, count in counts.items():
            j = self.word2id[m]
            tf = count
            df = self.vocab[m]["df"]
            # On ajoute +1 au dénominateur pour lisser le calcul (laplace smoothing)
            idf = math.log(self.nb_docs / (df + 1))
            vec[j] = tf * idf

        return vec

    def __cosinus(self, vq, vd_sparse):
        """
        ÉTAPE 6 : Mesure de similarité.
        On utilise la similarité cosinus (produit scalaire normalisé par les normes).
        Contrairement à une distance euclidienne, le cosinus mesure l'angle entre
        les vecteurs : cela permet de comparer des textes de longueurs différentes.
        """
        # Produit scalaire entre le vecteur dense (requête) et creux (document)
        num = vd_sparse.dot(vq)[0]

        # Calcul des normes euclidiennes (longueur des vecteurs)
        n1 = np.linalg.norm(vq)
        n2 = math.sqrt(vd_sparse.multiply(vd_sparse).sum())

        if n1 == 0 or n2 == 0:
            return 0

        return num / (n1 * n2)

    def search(self, mots, k=5):
        """
        ÉTAPE 7 : Moteur de recherche (Ranking).
        On compare la requête à chaque document du corpus.
        On trie par score décroissant pour renvoyer les 'k' meilleurs résultats.
        Retourne un DataFrame Pandas pour faciliter l'affichage dans l'interface.
        """
        vq = self.__query_to_vector(mots)
        scores = []

        # On calcule le score de chaque document
        for i in range(self.nb_docs):
            vd = self.mat_TFIDF.getrow(i)
            s = self.__cosinus(vq, vd)
            scores.append(s)

        # Structuration des résultats pour la vue
        df = pd.DataFrame({
            "doc_id": list(self.docs.keys()),
            "score": scores,
            "titre": [self.docs[i].titre for i in self.docs],
            "auteur": [self.docs[i].auteur for i in self.docs]
        })

        # Tri par pertinence (score le plus haut en premier)
        df = df.sort_values(by="score", ascending=False)
        return df.head(k)