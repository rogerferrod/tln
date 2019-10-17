"""
Esercitazione Conecpt Similarity
calcola similarità (usando 3 metriche) su coppie di termini
calcola inoltre indici di correlazione (Pearson e Spearman)
"""

__author__ = 'Davide Giosa, Roger Ferrod, Simone Cullino'

from optparse import OptionParser
import matplotlib.pyplot as plt
import sys
import time

from src.Esercitazione1.WordNetDriver import WordNetDriver
from src.Esercitazione1.Metrics import Metrics
from src.Esercitazione1.Indeces import *


def parse_csv(path):
    """
    Parsifica file di input composta da coppia di termini annotati manualmente
    :param path: percorso file di input
    :return: [(w1, w2, gold)]
    """
    couple_list = []
    with open(path, 'r') as fileCSV:
        for line in fileCSV.readlines()[1:]:
            temp = line.split(",")
            gold_value = temp[2].replace('\n', '')
            couple_list.append((temp[0], temp[1], float(gold_value)))

    return couple_list


def main():
    global options

    couple_list = parse_csv(options.input)
    print(couple_list)

    wnd = WordNetDriver()

    similarities = []  # lista di liste di similarità, una lista per ogni metrica
    metric_obj = Metrics(wnd)
    start_time = time.time()
    metrics = list(zip(*metric_obj.get_all()))

    to_remove = []
    count = 0  # per contare le coppie di sensi totali
    for f in metrics[0]:
        sim_metric = []  # lista di similirtà per questa metrica
        i = 0
        for t in couple_list:
            ss1 = WordNetDriver.get_synsets(t[0])
            ss2 = WordNetDriver.get_synsets(t[1])
            senses = [ss1, ss2]
            maxs = []  # lista di similarita tra sensi
            for s1 in senses[0]:
                for s2 in senses[1]:
                    count += 1
                    maxs.append(f(s1, s2))
            if len(maxs) == 0:  # parole prive di sensi (e.g nomi propri)
                maxs = [-1]
                to_remove.append(i)
            sim_metric.append(max(maxs))
            i += 1
        similarities.append(sim_metric)

    end_time = time.time()
    print("{0} combinazioni di sensi".format(count))
    print("{0} secondi".format(end_time - start_time))

    for i in range(len(couple_list)):
        if i in to_remove:
            del couple_list[i]
            for s in range(len(similarities)):
                del similarities[s][i]

    golden = [x[2] for x in couple_list]
    pearson_list = []
    spearman_list = []
    for i in range(len(metrics[1])):
        yy = similarities[i]
        pearson_list.append(pearson_index(golden, yy))
        spearman_list.append(spearman_index(golden, yy))
        draw_plot(i, metrics[1][i], golden, yy, pearson_list[i], spearman_list[i])

    with open(options.output + 'Es1_Results.txt', "w") as out:
        out.write("w1, w2 | m1, \tm2, \tm3 | gold\n")
        for i in range(len(couple_list)):
            out.write("{0}, {1} | {2:.2f}, \t{3:.2f}, \t{4:.2f} | {5}\n".format(couple_list[i][0], couple_list[i][1],
                                                                                similarities[0][i], similarities[1][i],
                                                                                similarities[2][i],
                                                                                couple_list[i][2],
                                                                                )
                      )

    with open(options.output + 'Es1_Indeces.txt', "w") as out:
        for i in range(len(pearson_list)):
            out.write("m" + str(i + 1) + " | Pearson Index: " + str(pearson_list[i]) + " | Spearman Index: " + str(
                spearman_list[i]) + "\n")


def draw_plot(id, metrics_name, list_gold_value, list_similarity, p_index_value, s_index_value):
    """
    Disegna grafico dati, asse x = golden value, asse y = concept similarity
    :param id: id figura
    :param metrics_name: nome metrica usata
    :param list_gold_value: lista di golden value
    :param list_similarity: lista di similarità
    :param p_index_value: Pearson index
    :param s_index_value: Spearman index
    """

    fig = plt.figure(id)
    plt.title(metrics_name)
    p_index_value = str(p_index_value)
    s_index_value = str(s_index_value)
    plt.text(0.5, 0.5, 'Pearson Index = ' + p_index_value[0:6] + '\n' + 'Spearman Index = ' + s_index_value[0:6])
    plt.plot(list_gold_value, list_similarity, 'o', color='#99ccff')
    plt.xlabel("Gold Value")
    plt.legend(loc='upper left')
    plt.ylabel("Concept Similarity")
    plt.grid(linestyle='--')

    fig.tight_layout()
    plt.savefig(options.output + '/' + str(id) + '.png', bbox_inches='tight')


if __name__ == "__main__":
    print("Concept Similarity")

    argv = sys.argv[1:]
    parser = OptionParser()

    parser.add_option("-i", "--input", help='input file', action="store", type="string", dest="input",
                      default="../../input/WordSim353.csv")

    parser.add_option("-o", "--output", help='output directory', action="store", type="string", dest="output",
                      default="../../output/Es1/")

    (options, args) = parser.parse_args()

    if options.input is None:
        print("Missing mandatory parameters")
        sys.exit(2)

    main()
