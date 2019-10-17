"""
Esercitazione text summarization
Riassume i testi in input utilizzando diverse tecniche di estrazione del topic
"""

__author__ = 'Davide Giosa, Roger Ferrod, Simone Cullino'

from optparse import OptionParser
import sys
from pathlib import Path

from src.Esercitazione3 import Topics


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
        for line in file.readlines():
            splits = line.split(";")
            vector_dict = {}

            for term in splits[2:]:
                k = term.split("_")
                if len(k) > 1:
                    vector_dict[k[0]] = k[1]

            nasari_dict[splits[1].lower()] = vector_dict

    return nasari_dict


def summarization(article, nasari_dict, topic_extractor, perc):
    """
    Applica riduzione articolo secondo la funzione di estrazione del topic
    :param article: rappresentazione articolo
    :param nasari_dict: dizionario Nasari
    :param topic_extractor: handle funzione estrazione del topic (e.g opp)
    :param perc: percentuale di riduzione
    :return: articolo ridotto
    """

    topics = topic_extractor(article, nasari_dict)

    paragraphs = []
    i = 0
    for par in article['body'][1:]:
        context = Topics.create_context(par, nasari_dict)
        paragraph_wo = 0  # media della Weighted Overlap all'interno del paragrafo

        for w in context:
            topic_wo = 0  # media Weighted Overlap del contesto generato a partire dal topic
            for vect in topics:
                topic_wo += weighted_overlap(w, vect)
            topic_wo /= len(topics)
            paragraph_wo += topic_wo

        if len(context) > 0:
            paragraph_wo /= len(context)
            paragraphs.append((i, paragraph_wo, par))
        i += 1

    limit = int(round((perc / 100) * len(paragraphs), 0))

    # ordina per punteggio e prende i primi 'limit'
    new_article = sorted(paragraphs, key=lambda x: x[1], reverse=True)[:limit]
    # ripristina ordine originale
    new_article = sorted(new_article, key=lambda x: x[0], reverse=True)
    # elimina stutture di supporto (ad ogni paragrafo abbiamo associato un punteggio)
    new_article = list(map(lambda x: x[2], new_article))

    new_article = [article['body'][0]] + new_article
    return new_article


def read_article(file):
    """
    Parsifica articolo (file di testo txt)
    :param file: file in input (articolo)
    :return: dizionario {genre:genere del testo, body: lista di paragrafi (il primo è il titolo)}
    """

    body = []
    article = {'genre': 'unknown', 'body': body}
    data = file.read_text(encoding='utf-8')
    lines = data.split('\n')

    for line in lines:
        if line != '' and line[0] == '@':
            article['genre'] = line.split(':')[1]
        elif line != '' and '#' not in line:
            line = line[:-1]
            body.append(line)

    return article


def main():
    global options

    nasari = parse_nasari()

    path = Path(options.input)
    recursive = './*.txt'
    files_articles = list(path.glob(recursive))

    for file in files_articles:
        article = read_article(file)

        for f in Topics.get_all():
            new_article = summarization(article, nasari, f[0], options.perc)
            name = article['body'][0].replace(':', '')
            with open(options.output + f[1] + '-' + name + '.txt', 'w', encoding='utf-8') as out:
                for p in new_article:
                    out.write(p + '\n')


if __name__ == "__main__":
    print('Summaritation')

    argv = sys.argv[1:]
    parser = OptionParser()

    parser.add_option("-i", "--input", help='input article', action="store", type="string", dest="input",
                      default="../../input/text_data/")

    parser.add_option("-n", "--nasari", help='nasari file', action="store", type="string", dest="nasari",
                      default="../../input/dd-small-nasari-15.txt")

    parser.add_option("-o", "--output", help='output directory', action="store", type="string", dest="output",
                      default="../../output/Es3/")

    parser.add_option("-p", "--perc", help='reduction perc', action="store", type="int", dest="perc",
                      default="50")

    (options, args) = parser.parse_args()

    if options.input is None or options.nasari is None or options.perc is None:
        print("Missing mandatory parameters")
        sys.exit(2)

    print('Reduction ' + str(options.perc) + '%')

    main()
