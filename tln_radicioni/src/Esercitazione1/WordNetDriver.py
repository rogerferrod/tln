"""
La seguente classe implementa il driver per accedere alla risorsa WordNet
Nel costruttore viene eseguito il calcolo della profondità massima del grafo,
in modo da non doverla richiedere in futuro (l'operazione è molto onerosa)
"""

__author__ = 'Davide Giosa, Roger Ferrod, Simone Cullino'

from nltk.corpus import wordnet as wn


class WordNetDriver:

    def __init__(self):
        self.depth_max = self.depth_max()

    def depth_path(self, synset, lcs):
        """
        :param synset: synset di cui calcolare i path
        :param lcs: primo senso comune
        :return: il path minimo che contiene lcs
        """

        paths = synset.hypernym_paths()
        paths = list(filter(lambda x: lcs in x, paths))  # path che contengono lcs
        return min(len(path) for path in paths)

    def lowest_common_subsumer(self, synset1, synset2):
        """
        :param synset1: syn1 da cui prendere lcs
        :param synset2: syn2 da cui prendere lcs
        :return: il primo lcs comune
        """

        if synset1 == synset2:
            return synset1

        commons = []
        for h in synset1.hypernym_paths():
            for k in synset2.hypernym_paths():
                zipped = list(zip(h, k))  # unisce 2 liste in una lista di tuple
                common = None
                for i in range(len(zipped)):
                    if zipped[i][0] != zipped[i][1]:
                        break
                    common = (zipped[i][0], i)

                if common is not None and common not in commons:
                    commons.append(common)

        if len(commons) <= 0:
            return None

        commons.sort(key=lambda x: x[1], reverse=True)
        # commons_api = synset1.lowest_common_hypernyms(synset2)
        return commons[0][0]

    def distance(self, synset1, synset2):
        """
        :param synset1: syn1 di cui calcolare la distanza con syn2
        :param synset2: syn2 di cui calcolare la distanza con syn1
        :return: distanza tra i due sensi
        """

        lcs = self.lowest_common_subsumer(synset1, synset2)
        lists_synset1 = synset1.hypernym_paths()
        lists_synset2 = synset2.hypernym_paths()

        if lcs is None:
            return None

        # path da lcs alla radice
        lists_lcs = lcs.hypernym_paths()
        set_lcs = set()
        for l in lists_lcs:
            for i in l:
                set_lcs.add(i)
        set_lcs.remove(lcs)  # nodi da lcs (escluso) alla radice

        # path dal synset fino all'lcs
        lists_synset1 = list(map(lambda x: [y for y in x if y not in set_lcs], lists_synset1))
        lists_synset2 = list(map(lambda x: [y for y in x if y not in set_lcs], lists_synset2))

        # path che contengono lcs
        lists_synset1 = list(filter(lambda x: lcs in x, lists_synset1))
        lists_synset2 = list(filter(lambda x: lcs in x, lists_synset2))

        return min(list(map(lambda x: len(x), lists_synset1))) + min(list(map(lambda x: len(x), lists_synset2))) - 2

    @staticmethod
    def depth_max():
        """
        :return: la profondità massima dell'albero di WordNet (20)
        """

        return max(max(len(path) for path in sense.hypernym_paths()) for sense in wn.all_synsets())

    @staticmethod
    def get_synsets(word):
        """
        :param word: parola di cui cercare il senso
        :return: lista di sensi (Synset) associati alla parola
        """

        return wn.synsets(word)
