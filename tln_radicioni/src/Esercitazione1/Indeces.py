"""
Il seguente modulo contiene le implementazione degli indici di correlazione
"""

__author__ = 'Davide Giosa, Roger Ferrod, Simone Cullino'

import numpy


def pearson_index(x, y):
    """
    :param x: golden value
    :param y: lista similarità
    :return: indice di correlazione di Pearson
    """

    mu_x = numpy.mean(x)
    mu_y = numpy.mean(y)
    std_dev_x = numpy.std(x)
    std_dev_y = numpy.std(y)

    modified__x = [elem - mu_x for elem in x]
    modified__y = [elem - mu_y for elem in y]

    num = numpy.mean(numpy.multiply(modified__x, modified__y))
    denum = std_dev_x * std_dev_y

    return num / denum


def spearman_index(x, y):
    """
    :param x: golden value
    :param y: lista similarità
    :return: indice di correlazione di Spearman
    """

    rank__x = define_rank(x)
    rank__y = define_rank(y)

    return pearson_index(rank__x, rank__y)


def define_rank(x):
    """
    :param x: vettore numerico
    :return: lista di rank corrispondenti al vettore di input (secondo l'ordine di input)
    """

    x_couple = [(x[i], i) for i in range(len(x))]

    x_couple_sorted = sorted(x_couple, key=lambda x: x[0])
    list_result = [y for (x, y) in x_couple_sorted]
    return list_result
