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
        Construit un vocabulaire :
        mot -> { id, total_occ, df }
        """
        vocab = {}
        next_id = 0

        for d in self.docs.values():
            propre = self.corpus.nettoyer_texte(d.texte)
            mots = propre.split()

            for m in mots:
                if m not in vocab:
                    vocab[m] = {
                        "id": next_id,
                        "total_occ": 0,
                        "df": 0
                    }
                    next_id += 1

        return vocab


    def __build_TF_matrix(self):
        """
        Construit la matrice TF en sparse CSR.
        """
        rows, cols, data = [], [], []

        for doc_id, d in self.docs.items():
            propre = self.corpus.nettoyer_texte(d.texte)
            mots = propre.split()

            compteur = {}
            for m in mots:
                if m in self.vocab:
                    compteur[m] = compteur.get(m, 0) + 1

            for m, c in compteur.items():
                rows.append(doc_id)
                cols.append(self.vocab[m]["id"])
                data.append(c)

        return csr_matrix(
            (data, (rows, cols)),
            shape=(self.nb_docs, len(self.vocab))
        )


    def __compute_vocab_stats(self):
        """
        Met à jour total_occ et df pour chaque mot du vocabulaire.
        """
        for mot, info in self.vocab.items():
            j = info["id"]
            col = self.mat_TF[:, j]

            info["total_occ"] = int(col.sum())
            info["df"] = col.count_nonzero()


    def __build_TFIDF_matrix(self):
        """
        Construit la matrice TF-IDF selon la formule du TD.
        """
        rows, cols, data = [], [], []

        N = self.nb_docs
        TF = self.mat_TF

        for i in range(N):
            row = TF.getrow(i)
            indices = row.indices
            values = row.data

            for j, tf in zip(indices, values):
                df = self.vocab[self.id2word[j]]["df"]

                if df > 0:
                    idf = math.log(N / df)
                    val = tf * idf
                    rows.append(i)
                    cols.append(j)
                    data.append(val)

        return csr_matrix((data, (rows, cols)), shape=TF.shape)


    def __query_to_vector(self, mots):
        """
        Transforme la requête utilisateur en vecteur TF-IDF.
        """
        # Nettoyer la requête comme les documents
        mots_nettoyes = self.corpus.nettoyer_texte(mots).split()
        vec = np.zeros(len(self.vocab))

        # Calcul du TF dans la requête
        counts = {}
        for m in mots_nettoyes:
            if m in self.word2id:
                counts[m] = counts.get(m, 0) + 1

        # Transformation en TF-IDF
        for m, count in counts.items():
            j = self.word2id[m]
            tf = count
            # Utiliser le DF stocké dans le vocabulaire pour le calcul de l'IDF
            df = self.vocab[m]["df"]
            idf = math.log(self.nb_docs / (df + 1)) # +1 pour éviter division par 0
            vec[j] = tf * idf

        return vec


    def __cosinus(self, vq, vd_sparse):
        """
        Calcule le cosinus entre :
            - vq : vecteur numpy
            - vd_sparse : ligne TF-IDF du document (csr_matrix)
        """
        # produit scalaire
        num = vd_sparse.dot(vq)[0]

        n1 = np.linalg.norm(vq)
        n2 = math.sqrt(vd_sparse.multiply(vd_sparse).sum())

        if n1 == 0 or n2 == 0:
            return 0

        return num / (n1 * n2)


    def search(self, mots, k=5): # ne fonctionne pas, à réparer, le score semble avoir un problème
        """
        Renvoie les k documents les plus proches d’une requête.
        """
        vq = self.__query_to_vector(mots)
        scores = []

        for i in range(self.nb_docs):
            vd = self.mat_TFIDF.getrow(i)
            s = self.__cosinus(vq, vd)
            scores.append(s)

        df = pd.DataFrame({
            "doc_id": list(self.docs.keys()),
            "score": scores,
            "titre": [self.docs[i].titre for i in self.docs],
            "auteur": [self.docs[i].auteur for i in self.docs]
        })

        df = df.sort_values(by="score", ascending=False)
        return df.head(k)

# Test
c = Corpus("Trump")
se = SearchEngine(c)
print(se.search("PUBLIC SERVICE ANNOUNCEMENT"))