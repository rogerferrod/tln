"""
Lesk module
provides an implementation of the lesk algorithm and a set of utilies methods

Accuracy: 47%  (SemCor)
"""

__author__ = 'Davide Giosa, Roger Ferrod, Simone Cullino'

import nltk
from nltk.corpus import wordnet as wn
from nltk.corpus import stopwords


def find_synonims(sense):
    """
    :param sense: synset di cui trovare i sinonimi
    :return: lista di sinonimi
    """

    synonyms = []
    for l in sense.lemmas():
        synonyms.append(l.name())

    return synonyms


def bag_of_word(sent):
    """
    Transforms the given sentence according to the bag of words approach,
    apply lemmatization, stop words and punctuation removal

    :param sent: sentence
    :return: bag of words
    """

    stop_words = set(stopwords.words('english'))
    punct = {',', ';', '(', ')', '{', '}', ':', '?', '!'}
    wnl = nltk.WordNetLemmatizer()
    tokens = nltk.word_tokenize(sent)
    tokens = list(filter(lambda x: x not in stop_words and x not in punct, tokens))
    return set(wnl.lemmatize(t) for t in tokens)  # siamo sicuri che non servano le ripetizioni?


def compute_overlap(signature, context):
    """
    computes the number of words in common between signature and context

    :param signature: bag of words of the signature (e.g. definitions + examples)
    :param context: bag of words of the context (e.g. sentence)
    :return: number of elements in commons
    """

    return len(signature & context)


def lesk(word, sentence):  # input frase e parola e output senso della parola
    """
    Implementazione dell'algoritmo lesk.
    Data una parola ed una frase in cui compare, ritorna il miglior senso della parola

    :param word: parola da disambiguare
    :param sentence: frase in cui compare
    :return: miglior senso di quella parola
    """

    senses = wn.synsets(word)
    if len(senses) <= 0:
        return None

    best_sense = senses[0]
    max_overlap = 0
    context = bag_of_word(sentence)

    for sense in senses:
        signature = bag_of_word(sense.definition())
        examples = sense.examples()
        for ex in examples:
            signature = signature.union(bag_of_word(ex))  # bag of words of definition and examples
        overlap = compute_overlap(signature, context)
        if overlap > max_overlap:
            max_overlap = overlap
            best_sense = sense

    return best_sense


def get_sense_index(word, sense):
    """
    Given a ambiguous word and a sense of this word,
    it returns the corresponding index of the sense in the synsets list associated with the word
    indeces starts with 1

    :param word: ambiguous word (with more that 1 sense)
    :param sense: sense of the word
    :return: index of the sense in the synsets list of the word
    """

    senses = wn.synsets(word)
    return senses.index(sense) + 1
