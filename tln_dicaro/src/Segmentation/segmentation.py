"""
Dato un testo suddividerlo in sezioni

9 sezioni:
tokens -    titolo -                           seq gap
0-1499		dichiarazione indipendenza		    60
1500-2062	The United States Bill of Rights.	82.52
2063-3653	JFK's Inaugural Address			    146.16
3654-3998	Lincoln's Gettysburg Address		159.96
3999-9146	costituzione				        365.88
9147-10549	Give Me Liberty Or Give Me Death	422
10550-10902	The Mayflower Compact			    436.12
10903-11711	Lincoln's Second Inaugural Address	468.48
11712-		Lincoln's First Inaugural Address

619 frasi
25 parole in media per frase
"""

__author__ = 'Roger Ferrod'

from optparse import OptionParser
import sys
import nltk
from nltk.corpus import stopwords
import numpy as np
import math
import matplotlib.pyplot as plt
import pandas as pd
from scipy import signal

# golden values
separators = [60, 83, 146, 160, 366, 422, 436, 468]


def compute_overlap(signature, context):
    """
    :param signature: firma del testo (BoW)
    :param context: contesto (BoW)
    :return: l'interesezione insiemistica tra i due insiemi
    """

    return signature & context


def rank(x, v):
    """
    :param x: componente vettore
    :param v: vettore Nasari
    :return: rank del componente (posizione)
    """

    for i in range(len(v)):
        if v[i] == x:
            return i + 1


def weighted_overlap(v1, v2):
    """
    Implementazione Weight Overlap (Pilehvar et al.)
    :param v1: vettore Nasari (topic)
    :param v2: vettore Nasari (paragrafo)
    :return: square-rooted Weighted Overlap, 0 se non c'è sovrapposizione
    """

    # v = {"w":n, "w":n, "w":n, "w":n}
    overlap_keys = compute_overlap(v1.keys(), v2.keys())

    overlaps = list(overlap_keys)

    if len(overlaps) > 0:
        den = sum(1 / (rank(q, list(v1)) + rank(q, list(v2))) for q in overlaps)  # sum 1/(rank() + rank())
        num = sum(list(map(lambda x: 1 / (2 * x), list(range(1, len(overlaps) + 1)))))  # sum 1/(2*i)

        return den / num

    return 0


def parse_nasari():
    """
    Parsifica il file di input Nasari (rappresentazione Lexical)
    :return: dizionario {word: {term:score}}
    """

    global options

    nasari_dict = {}
    with open(options.nasari, 'r', encoding="utf8") as file:
        for line in file:
            # splits = line.split(";")
            splits = line.split("\t")
            vector_dict = {}

            for term in splits[2:options.limit]:
                k = term.split("_")
                if len(k) > 1:
                    vector_dict[k[0]] = k[1]

            nasari_dict[splits[1].lower()] = vector_dict

    return nasari_dict


def read(path):
    with open(path) as file:
        lines = file.readlines()
    return ''.join(lines)


def tokenize(text):
    """
    suddivide il testo in gruppi di w parole
    :param text: testo
    :return: lista di sequenze
    """
    global options

    sequences = []
    text = text.lower()
    tokens = nltk.word_tokenize(text)
    j = 0
    for i in range(options.w, len(tokens), options.w):
        sequences.append(tokens[j:i])
        j = i

    print(str(len(sequences)) + ' sequences')
    return sequences


def bag_of_word(tokens):
    """
    Ritorna la rappresentazione Bag of Word del testo
    applica lemmatizzazione, rimozione punteggiatura e rimozione stop-words
    rimuove i duplicati
    :param text: stringa di testo
    :return: rappresentazione BoW del testo
    """

    stop_words = set(stopwords.words('english'))
    punct = {',', ';', '(', ')', '{', '}', ':', '?', '!', '*'}
    wnl = nltk.WordNetLemmatizer()
    tokens = list(filter(lambda x: x not in stop_words and x not in punct, tokens))
    return set(wnl.lemmatize(t) for t in tokens)


def create_vectors(tokens, nasari):
    """
    Crea una lista di vettori Lexical Nasari (dizionaro {term:score})
    associati ad ogni termine del testo
    :param text: stringa di testo
    :param nasari: dizionario Nasari
    :return: lista di vettori Nasari
    """

    tokens = bag_of_word(tokens)
    vectors = []
    for word in tokens:
        if word in nasari.keys():
            vectors.append(nasari[word])

    return vectors


def main():
    global options

    # Input
    nasari = parse_nasari()
    text = read(options.input)

    # tokenize
    sequences = tokenize(text)

    # compute similarity neighbors
    similarities = list(np.zeros(len(sequences)))
    for i in range(1, len(sequences) - 1):
        prev = create_vectors(sequences[i - 1], nasari)
        current = create_vectors(sequences[i], nasari)
        next = create_vectors(sequences[i + 1], nasari)

        # compute square root weighted overlap
        similarity = []
        for x in prev:
            for w in current:
                similarity.append(math.sqrt(weighted_overlap(x, w)))
        left = max(similarity) if len(similarity) > 0 else 0

        similarity = []
        for x in next:
            for w in current:
                similarity.append(math.sqrt(weighted_overlap(x, w)))
        right = max(similarity) if len(similarity) > 0 else 0

        similarities[i] = (left + right) / 2

    del nasari

    # plot
    length = len(similarities)
    x = np.arange(0, length, 1)
    y = np.array(similarities)

    short = int(0.016 * length)
    long = int(0.08 * length)
    very_long = int(0.16 * length)
    span = length / (options.k + 1)

    # moving average
    data = pd.DataFrame(data=y)
    short_rolling = data.rolling(window=short).mean()
    long_rolling = data.rolling(window=long).mean()
    ema_very_long = data.ewm(span=very_long, adjust=False).mean()

    # local minimum
    f = np.array(ema_very_long.to_numpy()).reshape((length,))
    inv_data_y = f * (-1)
    valley = signal.find_peaks_cwt(inv_data_y, np.arange(1, span))

    '''
    couples = list(zip(valley, f[valley]))
    
    # ordina per punteggio e prende i primi 'limit'
    valley = sorted(couples, key=lambda x: x[1], reverse=False)[:options.k]
    # ripristina ordine originale
    valley = sorted(valley, key=lambda x: x[0], reverse=True)
    # elimina stutture di supporto (ad ogni paragrafo abbiamo associato un punteggio)
    valley = list(map(lambda x: x[0], valley))
    '''

    fig, ax = plt.subplots()
    ax.plot(x, y, label='blocks cohesion', color='c')
    ax.plot(x, short_rolling, label=str(short) + '-gaps SMA', color='y')
    ax.plot(x, long_rolling, label=str(long) + '-gaps SMA', color='g')
    ax.plot(x, ema_very_long, label=str(very_long) + '-gaps EMA', color='r')
    plt.plot(x[valley], f[valley], "o", label="local minimum (" + str(span) + " span)", color='r')

    for x in separators:
        ax.axvline(x, color='k', linewidth=1)

    ax.set(xlabel='tokens sequence gap', ylabel='similarity',
           title='Block similarity')
    ax.grid()

    ax.legend(loc='best')
    plt.show()


if __name__ == "__main__":
    print('Segmentation')

    argv = sys.argv[1:]
    parser = OptionParser()

    parser.add_option("-i", "--input", help='input', action="store", type="string", dest="input",
                      default="../../input/text.txt")

    parser.add_option("-o", "--output", help='input', action="store", type="string", dest="output",
                      default="../../output/")

    '''parser.add_option("-n", "--nasari", help='nasari file', action="store", type="string", dest="nasari",
                      default="../../resources/dd-small-nasari-15.txt")'''

    parser.add_option("-n", "--nasari", help='nasari file', action="store", type="string", dest="nasari",
                      default="../../resources/NASARI_lexical_english.txt")

    parser.add_option("-l", "--limit", help='nasari dimensions', action="store", type="int", dest="limit",
                      default="14")

    parser.add_option("-w", help='tokens sequence size', action="store", type="int", dest="w",
                      default="25")

    parser.add_option("-k", help='number of segments', action="store", type="int", dest="k",
                      default="9")

    (options, args) = parser.parse_args()

    if options.input is None or options.nasari is None or options.k is None or options.w is None:
        print("Missing mandatory parameters")
        sys.exit(2)

    main()
