"""
Il seguente modulo contiene le implementazioni delle metriche usate per il calcolo della similarità
"""

__author__ = 'Davide Giosa, Roger Ferrod, Simone Cullino'

from math import log


class Metrics:
    def __init__(self, wnd):
        self.wnd = wnd

    def wu_palmer_metric(self, synset1, synset2):
        lcs = self.wnd.lowest_common_subsumer(synset1, synset2)
        if lcs is None:
            return 0

        depth_lcs = self.wnd.depth_path(lcs, lcs)
        depth_s1 = self.wnd.depth_path(synset1, lcs)
        depth_s2 = self.wnd.depth_path(synset2, lcs)
        res = (2 * depth_lcs) / (depth_s1 + depth_s2)
        return res * 10

    def shortest_path_metric(self, synset1, synset2):
        max_depth = self.wnd.depth_max
        len_s1_s2 = self.wnd.distance(synset1, synset2)
        if len_s1_s2 is None:
            return 0
        res = 2 * max_depth - len_s1_s2
        return (res / 40) * 10

    def leakcock_chodorow_metric(self, synset1, synset2):
        max_depth = self.wnd.depth_max
        len_s1_s2 = self.wnd.distance(synset1, synset2)
        if len_s1_s2 is None:
            return 0
        if len_s1_s2 == 0:
            len_s1_s2 = 1
            res = -(log((len_s1_s2 / ((2 * max_depth) + 1)), 10))
        else:
            res = -(log((len_s1_s2 / (2 * max_depth)), 10))
        return (res / (log(2 * self.wnd.depth_max + 1, 10))) * 10

    def get_all(self):
        return [(self.wu_palmer_metric, "Wu & Palmer"), (self.shortest_path_metric, "Shortest Path"),
                (self.leakcock_chodorow_metric, "Leakcock & Chodorow")]
