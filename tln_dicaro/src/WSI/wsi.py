import nltk
from nltk.corpus import brown
from nltk.corpus import wordnet as wn
from nltk.stem import WordNetLemmatizer
from sklearn.cluster import DBSCAN
from sklearn.cluster import OPTICS
from sklearn.cluster import KMeans
from sklearn.decomposition import NMF
from sklearn.decomposition import TruncatedSVD
from sklearn.decomposition import PCA
from sklearn.feature_extraction.text import TfidfVectorizer
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np
import pandas as pd


def text_extraction(couple):
    lemmatizer = WordNetLemmatizer()
    list_sent = brown.sents()  # (categories=['news', 'hobbies', 'reviews', 'adventure', 'government', 'editorial','learned','humor',])
    sentences = []
    w1_count = 0
    w2_count = 0

    for sent in list_sent:
        for word in sent:
            word = lemmatizer.lemmatize(word)
            if word == couple[0]:
                w1_count += 1
                sentences.append(sent)
            elif word == couple[1]:
                w2_count += 1
                sentences.append(sent)

    return sentences, (w1_count, w2_count)


def text_substitute(sentences, couple, pseudoword):
    result = set()
    for s in sentences:
        sent = [pseudoword if w == couple[0] or w == couple[1] else w for w in s]
        sentence = ' '.join(sent)
        result.add(sentence.strip())
    return list(filter(lambda x: pseudoword in x, result))


def vectorizer(sentences):
    # tf-idf vectorizer
    tfidf = TfidfVectorizer(use_idf=True, stop_words='english')
    matrix = tfidf.fit_transform(sentences)
    features = tfidf.get_feature_names()

    return matrix, features


def clustering(matrix):
    # clustering = DBSCAN(algorithm='auto', eps=0.85, metric='cosine').fit(matrix)
    # clusters = OPTICS(min_samples=5, metric='cosine').fit(matrix)
    clusters = KMeans(init='k-means++', n_clusters=3).fit(matrix)
    return clusters.labels_


def cluster_plot(matrix, cluster_labels, id):
    svd = TruncatedSVD(n_components=2)
    pos = svd.fit_transform(matrix)

    fig = plt.figure(id)
    xs, ys = pos[:, 0], pos[:, 1]
    colors = cm.rainbow(np.linspace(0, 1, len(set(cluster_labels))))
    colors[-1] = 0
    df = pd.DataFrame(dict(x=xs, y=ys, label=cluster_labels))
    groups = df.groupby('label')

    ax = fig.add_subplot(111)
    for name, group in groups:
        ax.plot(group.x, group.y, marker='o', linestyle='', ms=5, color=colors[name],
                mec='none')
        ax.set_aspect('auto')

    ax.set_xlabel(r'Coordinate 1', fontsize=15)
    ax.set_ylabel(r'Coordinate 2', fontsize=15)
    ax.set_title('Tf-idf Matrix (SVD)')
    ax.grid(True)

    # draw and save
    fig.tight_layout()
    plt.savefig('../../output/clusters.png', bbox_inches='tight')
    plt.show()


def plot(matrix, title, id):
    svd = TruncatedSVD(n_components=2)
    pos = svd.fit_transform(matrix)
    # model = NMF(n_components=2, init='random', random_state=0)
    # pos = model.fit_transform(matrix)

    fig = plt.figure(id)
    xs, ys = pos[:, 0], pos[:, 1]
    plt.plot(xs, ys, marker='o', linestyle='', ms=5, mec='none')
    plt.xlabel(r'Coordinate 1', fontsize=15)
    plt.ylabel(r'Coordinate 2', fontsize=15)
    plt.title('Tf-idf Matrix (' + title + ')')
    plt.grid(True)

    # draw and save
    fig.tight_layout()
    plt.savefig('../../output/plot-' + title + '.png', bbox_inches='tight')
    plt.show()


if __name__ == "__main__":
    # couple = ('employer', 'airport')
    # couple = ('year', 'employer')  # 4 sensi x 1
    couple = ('month', 'airport')  # 2 sensi x 1
    # couple = ('month', 'money')  # 2 sensi x 3
    # couple = ('month', 'economy')  # 2 sensi x 4

    pseudoword = couple[0] + '_' + couple[1]

    sentences, count = text_extraction(couple)
    sentences = text_substitute(sentences, couple, pseudoword)
    print(str(len(sentences)) + ' frasi')
    print('freq w1-w2: ' + str(count))

    # tf-idf
    tf_idf_matrix, features = vectorizer(sentences)
    print('tf-idf shape ' + str(tf_idf_matrix.shape))

    # LSA
    model = NMF(n_components=500, init='random', random_state=0)
    matrix = model.fit_transform(tf_idf_matrix)

    svd = TruncatedSVD(n_components=500)
    svd_matrix = svd.fit_transform(tf_idf_matrix)

    plot(matrix, 'NMF', 1)
    plot(svd_matrix, 'SVD', 2)

    # clustering

    matrix = svd_matrix

    labels = clustering(matrix)

    pd.set_option('display.max_colwidth', -1)
    df = pd.DataFrame(dict(sent=sentences, label=labels))
    groups = df.groupby('label')
    for name, group in groups:
        print('cluster ' + str(name))
        print(group.sent)
        print('---------------')

    cluster_plot(matrix, labels, 3)
