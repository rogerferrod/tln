"""
Il seguente modulo contiene le implementazioni delle tecniche di estrazione del topic
e alcuni metodi ausiliari
"""

__author__ = 'Davide Giosa, Roger Ferrod, Simone Cullino'

from nltk.corpus import stopwords
import nltk


def bag_of_word(text):
    """
    Ritorna la rappresentazione Bag of Word del testo
    applica lemmatizzazione, rimozione punteggiatura e rimozione stop-words
    rimuove i duplicati
    :param text: stringa di testo
    :return: rappresentazione BoW del testo
    """

    text = text.lower()
    stop_words = set(stopwords.words('english'))
    punct = {',', ';', '(', ')', '{', '}', ':', '?', '!'}
    wnl = nltk.WordNetLemmatizer()
    tokens = nltk.word_tokenize(text)
    tokens = list(filter(lambda x: x not in stop_words and x not in punct, tokens))
    return set(wnl.lemmatize(t) for t in tokens)


def create_vectors(topic, nasari):
    """
    Crea una lista di vettori Lexical Nasari (dizionario {term:score})
    associati ad ogni termine del topic (e.g titolo)
    :param topic: parole del topic
    :param nasari: dizionario NASARI
    :return: lista di vettori Nasari
    """

    vectors = []
    for word in topic:
        if word in nasari.keys():
            vectors.append(nasari[word])

    return vectors


def create_context(text, nasari):
    """
    Crea una lista di vettori Lexical Nasari (dizionaro {term:score})
    associati ad ogni termine del testo
    :param text: stringa di testo
    :param nasari: dizionario Nasari
    :return: lista di vettori Nasari
    """

    tokens = bag_of_word(text)
    vectors = []
    for word in tokens:
        if word in nasari.keys():
            vectors.append(nasari[word])

    return vectors


def title_topic(article, nasari):
    """
    Crea una lista di vettori Nasari a partire dal titolo dell'articolo
    :param article: articolo
    :param nasari: dizionario Nasari
    :return: lista vettori Nasari
    """

    title = article['body'][0]
    tokens = bag_of_word(title)
    vectors = create_vectors(tokens, nasari)
    return vectors


def opp_topic(article, nasari):
    """
    Crea una lista di vettori Nasari a partire dall'articolo, secondo la metodologia OPP

    OPP da Hovy, Lin (1997)
    newspaper
        OPP = [T1, P2S1, P3S1, P4S1, P1S1, P2S2, P3S2, P4S2, P5S1, P1S2, P1S2, P6S1]
    wsj
        OPP = [T1, P1S1, P1S2]

    :param article: articolo
    :param nasari: dizionario Nasari
    :return: lista vettori Nasari
    """

    sentences = []
    for p in article['body'][1:]:
        sents = nltk.sent_tokenize(p)
        sentences.append(sents)

    # newspaper
    news_opp = {'title': True,
                "opps": [(1, 1), (1, 2), (2, 1), (2, 2), (3, 1), (3, 2), (4, 1), (4, 2), (5, 1), (6, 1)]}

    # Wall Street Journal
    wsj_opp = {'title': True, "opps": [(1, 1), (1, 2)]}

    # "opps" corrisponde a (indice paragrafo, indice frase)
    # "title" = true se è necessario considerare anche il titolo

    vectors = []
    if article['genre'] == 'wsj':
        opp = wsj_opp
    elif article['genre'] == 'news':
        opp = news_opp
    else:
        opp = {'title': True, 'opps': []}

    if opp['title']:
        vectors = title_topic(article, nasari)
        for t in opp['opps']:
            p = t[0]  # indice paragrafo
            s = t[1]  # indice sentence
            if p < len(sentences) and s < len(sentences[p]):
                sent = sentences[t[0]][t[1]]
                vectors += create_vectors(sent, nasari)

    return vectors


def get_all():
    """
    :return: lista di funzioni, per ogni topic extractor
    """

    return [(title_topic, 'title'), (opp_topic, 'opp')]
