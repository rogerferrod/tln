"""
Esercitazione Concept Similarity
"""

__author__ = 'Davide Giosa, Roger Ferrod, Simone Cullino'

from optparse import OptionParser
import sys
from scipy.stats import pearsonr
from scipy.stats import spearmanr
import numpy as np
import requests
from sklearn.metrics.pairwise import cosine_similarity


def get_gloss(sense):
    """
    Esegue chiamate a BabelNet per ricavare le glossa (in italiano) del BabelSynset
    :param sense: BabelID del senso
    :return: glossa corrispondente
    """

    global options

    url = "https://babelnet.io/v5/getSynset"
    params = {
        'id': sense,
        'key': options.key,
        'targetLang': 'IT'
    }

    r = requests.get(url=url, params=params)
    data = r.json()

    if len(data["glosses"]) == 0:
        return "GLOSS INESISTENTE"
    else:
        return data["glosses"][0]["gloss"]


def parse_nasari():
    """
    Parsifica il file di input NASARI (rappresentazione Embedded)
    Ritorna un dizionario che associa ad ogni BabelID il vettore Nasari corrispondente
    e un dizionario lessicale che associa ad ogni BabelID il termine inglese corrispondente
    :return: {babelId: [values]}, {babelID: word_en}
    """

    global options

    nasari = {}
    babel_word_nasari = {}

    with open(options.nasari, 'r', encoding="utf8") as file:
        for line in file.readlines():
            lineSplitted = line.split()
            k = lineSplitted[0].split("__")
            babel_word_nasari[k[0]] = k[1]
            lineSplitted[0] = k[0]
            i = 1
            values = []
            while i < len(lineSplitted):
                values.append(float(lineSplitted[i]))
                i += 1
            nasari[lineSplitted[0]] = values

    return nasari, babel_word_nasari


def parse_italian_synset():
    """
    Parsifica SemEvalIT (ad ogni termine italiano è associato una lista di BabelID)
    :return: dizionario {word_it: [BabelID]}
    """

    global options
    sem_dict = {}
    synsets = []
    key = "first_step"
    with open(options.it_synset, 'r', encoding="utf8") as file:
        for line in file.readlines():
            line = line[:-1].lower()
            if "#" in line:
                line = line[1:]
                if key != "first_step":
                    sem_dict[key] = synsets
                key = line
                synsets = []
            else:
                synsets.append(line)
    return sem_dict


def parse_input(path):
    """
    Parsifica file annotazioni
    :param percorso del file di input
    :return: lista di termini annotati [((w1, w2), valore)]
    """

    annotation_list = []
    with open(path, 'r', encoding="utf-8-sig") as file:
        for line in file.readlines():
            splits = line.split("\t")
            key = (splits[0].lower(), splits[1].lower())
            value = splits[2].split("\n")
            annotation_list.append((key, float(value[0])))
    return annotation_list


def compute_interrate(v1, v2):
    """
    Calcola interrate agreement tra 2 vettori di annotazioni
    :param v1: vettore di annotazione (file 1)
    :param v2: vettore di annotazione (file 2)
    :return: media, indice pearson, indice spearman
    """

    means = []
    for i in range(len(v1)):
        means.append((v1[i] + v2[i]) / 2)
    return means, pearsonr(v1, v2)[0], spearmanr(v1, v2)[0]


def similarity_vectors(bn_list1, bn_list2, nasari_dict):
    """
    Calcola la similarità coseno tra 2 vettori Nasari (rappresentazione Embedded)
    Restituisce la coppia di sensi (BabelID) che massimizza tale similarità
    :param bn_list1: lista di babelID della parola 1
    :param bn_list2: lista di babelID della parola 2
    :param nasari_dict: dizionario di NASARI
    :return: la coppia di sensi che massimizza la cosine similarity
    """

    max_value = 0
    senses = (None, None)
    for bn1 in bn_list1:
        for bn2 in bn_list2:
            if bn1 in nasari_dict.keys() and bn2 in nasari_dict.keys():
                v1 = nasari_dict[bn1]
                v2 = nasari_dict[bn2]
                n1 = np.array(v1).reshape(1, len(v1))  # trasforma array in un np.array (numpy array)
                n2 = np.array(v2).reshape(1, len(v2))  # dimensione array: 1 x len(v)
                t = cosine_similarity(n1, n2)[0][0]
                if t > max_value:
                    max_value = t
                    senses = (bn1, bn2)
    return senses


if __name__ == "__main__":
    argv = sys.argv[1:]
    parser = OptionParser()

    parser.add_option("-n", "--nasari", help='nasari file', action="store", type="string", dest="nasari",
                      default="../../input/mini_NASARI.tsv")
    parser.add_option("-i", help='input annotation file', action="store", type="string", dest="annotation1",
                      default="../../input/annotation1.txt")
    parser.add_option("-u", help='input annotation file', action="store", type="string", dest="annotation2",
                      default="../../input/annotation2.txt")
    parser.add_option("-s", help='input parse italian synsset', action="store", type="string", dest="it_synset",
                      default="../../input/SemEval17_IT_senses2synsets.txt")
    parser.add_option("-o", "--output", help='output directory', action="store", type="string", dest="output",
                      default="../../output/Es4/")
    parser.add_option("-k", "--key", help='BabelNet API key', action="store", type="string", dest="key",
                      default="4791c99c-76fc-4c75-92f7-845f8ebe46c6")

    (options, args) = parser.parse_args()

    if options.annotation1 is None or options.annotation2 is None or options.nasari is None or options.it_synset is None:
        print("Missing mandatory parameters")
        sys.exit(2)

    nasari_dict, babel_word_nasari = parse_nasari()
    italian_senses_dict = parse_italian_synset()

    annotation1 = parse_input(options.annotation1)
    annotation2 = parse_input(options.annotation2)

    # coppie parole annotate
    c1 = list(zip(*annotation1))[0]
    c2 = list(zip(*annotation2))[0]

    # annotazioni
    v1 = list(zip(*annotation1))[1]
    v2 = list(zip(*annotation2))[1]

    avg, pearson, spearman = compute_interrate(v1, v2)

    print('Person: {0}, Spearman: {1}'.format(pearson, spearman))
    print('Media: {0}'.format(avg))

    annotation = list(zip(c1, avg))

    with open(options.output + 'Es4.txt', "w", encoding="utf-8") as out:
        for couple in annotation:
            key = couple[0]

            (s1, s2) = similarity_vectors(italian_senses_dict[key[0]], italian_senses_dict[key[1]], nasari_dict)
            out.write(str(key) + "\n")
            if s1 is not None and s2 is not None:
                out.write(str((s1, s2)) + "\n")
                gloss1 = get_gloss(s1)
                gloss2 = get_gloss(s2)
                out.write(gloss1 + "\n")
                out.write(gloss2 + "\n")
            else:
                out.write("None     None\n")
            out.write("-------------------------------------------------\n")
