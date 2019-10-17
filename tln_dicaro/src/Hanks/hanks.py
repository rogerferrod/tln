"""
Dato un verbo transitivo, si recuperano dal Brown Corpus n instaze in cui esso viene usato
Segue disambiguazione (Lesk - WordNet) sugli argomenti (subj, obj)
Calcolo frequenze incidenza dei supersensi dei fillers
"""

__author__ = 'Davide Giosa, Roger Ferrod, Simone Cullino'

from nltk.parse.corenlp import CoreNLPDependencyParser
from src.Hanks.DependencyGraph import DependencyGraph
from nltk.corpus import brown
from nltk.stem import WordNetLemmatizer
from src.Hanks.lesk import *

verbs = ['VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ']
verb = "meet"  # take, put, give, get, meet
subj_dept = ['nsubj', 'nsubjpass']
obj_dept = ['dobj', 'iobj']


# java -mx4g -cp "*" edu.stanford.nlp.pipeline.StanfordCoreNLPServer -port 9000 -timeout 15000

def text_extraction():
    """
    Analizza il Brown Corpus ed estrae le frasi contenenti il verbo desiderato
    :return: lista di frasi (ogni frase è una lista di parole)
    """

    lemmatizer = WordNetLemmatizer()
    list_sent = brown.sents()
    # list_sent = brown.sents(categories=['news'])

    sentences = []
    for sent in list_sent:
        tags = dict(nltk.pos_tag(sent))
        for word in sent:
            if tags[word] in verbs:
                word = lemmatizer.lemmatize(word, 'v')
                if word == verb:
                    sentences.append(sent)

    return sentences


def lemmatize(graph, tags):
    """
    Applica lemmatizzazione ai verbi nel grafo di dipendenze
    :param graph: grado a dipendenze
    :param tags: PoS della frase corrispondente
    :return: nuovo grafo lemmatizzato
    """

    lemmatizer = WordNetLemmatizer()
    new_dict = {}
    for k in graph.dict:
        word = graph.dict[k]
        if word in tags.keys() and tags[word] in verbs:
            new_dict[k] = lemmatizer.lemmatize(word, 'v')
        else:
            new_dict[k] = word

    return DependencyGraph(graph.graph, new_dict)


if __name__ == "__main__":
    fillers = []  # [(subj, obj, sentence)]
    sentences = []
    dependency_parser = CoreNLPDependencyParser(url="http://localhost:9000")

    print('extracting sentences...')
    list_word_sentences = text_extraction()
    for sent in list_word_sentences:
        sentence = ' '.join(sent)
        sentences.append(sentence.strip())

    sentences = [x.lower() for x in sentences]
    print(str(len(sentences)) + ' frasi')

    print('extracting fillers...')
    for sentence in sentences:
        # PoS tagging
        sentence = sentence.replace('.', '')
        tokens = nltk.word_tokenize(sentence)
        tags = dict(nltk.pos_tag(tokens))

        # syntactic parsing
        result = dependency_parser.raw_parse(sentence)
        dep = next(result)
        graph = DependencyGraph()
        graph.from_dot(dep.to_dot())

        # lemmatize
        lemmatized_graph = lemmatize(graph, tags)
        index = lemmatized_graph.get_index(verb)
        if len(index) <= 0:
            print('error in **' + sentence + '**')
            continue

        # adjacency list
        adjs = lemmatized_graph.get_directional_adj(index[0])
        adjs = list(filter(lambda x: x[1] in subj_dept or x[1] in obj_dept, adjs))

        # valency = 2
        if len(adjs) == 2:
            if adjs[0][1] in subj_dept:
                w1 = lemmatized_graph.dict[adjs[0][0]]
                w2 = lemmatized_graph.dict[adjs[1][0]]
            else:
                w1 = lemmatized_graph.dict[adjs[1][0]]
                w2 = lemmatized_graph.dict[adjs[0][0]]
            fillers.append((w1, w2, sentence))  # w1 = subj, w2 = obj

    tot = len(fillers)
    print(str(tot) + ' fillers')
    for f in fillers:
        print(f)
    print('----------------------------')

    semantic_types = {}  # {(s1, s2): count}
    for f in fillers:
        # WSD
        s1 = lesk(f[0], f[2])
        s2 = lesk(f[1], f[2])
        if s1 is not None and s2 is not None:
            # supersences
            t = (s1.lexname(), s2.lexname())

            # frequency
            if t in semantic_types.keys():
                semantic_types[t] = semantic_types[t] + 1
            else:
                semantic_types[t] = 1

    print('clusters')
    for k, v in sorted(semantic_types.items(), key=lambda x: x[1], reverse=True):
        print(k, v, '(' + str(round((v / tot) * 100, 2)) + '%)')
