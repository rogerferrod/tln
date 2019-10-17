from nltk import parse
import json
from anytree import AnyNode
from anytree.exporter import JsonExporter

from src.Utils import *
from optparse import OptionParser
import sys


def translate_word(word, prop=False):
    """
    Metodo per la traduzione 1:1
    :param word: parola in forma flessa da tradurre
    :param prop: TRUE = se è un nome proprio, di conseguenza non viene tradotto
    :return: la traduzione in italiano del parametro word
    """
    if not prop:
        with open('../resources/lex.txt') as json_file:
            lex = json.load(json_file)
        return lex[word]
    return word


def parser(sent, grammar):
    """
    Richiama il parser della libreria NLTK
    :param sent: frase da parsificare
    :param grammar: percorso della grammatica di riferimento
    :return: tutti i possibili alberi di parsficazione
    """
    cp = parse.load_parser(grammar, trace=0)  # trace=1 se verbose
    tokens = sent.split()
    trees = cp.parse(tokens)
    return trees


def create_node(id, type, parent, label=None, prop=None):
    """
    Metodo ausiliario per la crazione di nodi del proto-albero. Incapsula la funzione AnyNode
    :param id: id univoco del nodo
    :param type: tipo del nodo
    :param parent: nodo padre del nodo che si sta creando
    :param label: parola tradotta da inserire nel nodo (presente solo nelle foglie)
    :param prop: features del nodo (dizionario {'tipoFeatures': 'valore'})
    :return: id successivo disponibile, nodo creato
    """
    id += 1
    if label is not None and prop is not None:
        return id, AnyNode(a=str(id), b=type, c=label, d=str(prop), parent=parent)
    if label is not None and prop is None:
        return id, AnyNode(a=str(id), b=type, c=label, parent=parent)
    return id, AnyNode(a=str(id), b=type, d=str(prop), parent=parent)


def sentence_00(tree):
    """
        FRASE DEL TIPO: exists x.(obj(x), verb(subj,x))
        cioè semplice frase dichiarativa con soggetto, verbo (transitivo) e oggetto (diretto)
    """

    # cerchiamo il verbo
    # sappiamo dove trovarlo dalla semantica associata
    terms = get_semantics(tree)
    var_verb = terms[1 + (len(terms) - 2)]  # quando non ci sono i modificatori, la lista terms è lunga 2
    subj, var_obj = transtitive_parse(var_verb)
    verb = match_pred_pos(tree, var_verb)

    # cerchiamo l'oggetto
    occ_obj = find_occurencies(tree, var_obj)
    obj = list(filter(lambda x: 'N' == x['tag'], occ_obj))[0]  # tutto il resto saranno modificatori
    occ_obj.remove(obj)
    # il varbo comparirà sia in obj che in verb (xke è una funzione del tipo f(x,y))
    if verb in occ_obj:
        occ_obj.remove(verb)

    # soggetto
    subj = match_pred_pos(tree, subj)

    id = 0
    id, root = create_node(id, type="clause", parent=None, label=None, prop={"tense": verb['tns']})

    # soggetto
    id, subj_node = create_node(id, type="subj", parent=root,
                                label=translate_word(subj['pred'], subj['tag'] == 'PropN'))

    # oggetto
    id, child_obj = create_node(id, type="obj", parent=root)
    id, child3 = create_node(id, type="spec", label='il', parent=child_obj)
    id, child4 = create_node(id, type="noum", label=translate_word(obj['pred']), prop={"number": obj['num'],
                                                                                       "gen": obj['gen']},
                             parent=child_obj)
    for x in occ_obj:  # prendo tutti i modificatori, se ne sono rimasti
        id, child = create_node(id, type="modifier", label=translate_word(x['pred']), parent=child_obj)

    # verbo
    id, child5 = create_node(id, type="verb", label=translate_word(verb['pred']), parent=root)

    return root


def sentence_01(tree):
    """
        FRASE DEL TIPO: exists x.(exists e.(VP(e), exists z.(subj(x), complement(x,z))))
        cioè esiste un complemento che mette in relazione il soggetto con qualcosa..
        il complemento è datto da preposizione e NP
    """

    visited = set()
    # cerchiamo il verbo
    terms = get_semantics(tree)
    var_verb = terms[0]
    verb = match_pred_pos(tree, var_verb)
    event = str(var_verb.args[0])
    visited.add(event)

    # cerchiamo il soggetto
    var_subj = intranstitive_parse(tree, var_verb)
    visited.add(var_subj)

    mod_subj = find_occurencies(tree, var_subj)
    subj = list(filter(lambda x: 'N' == x['tag'], mod_subj))[0]
    mod_subj.remove(subj)

    # cerchiamo il complemento
    var_compl = get_all_variables(tree) - visited  # prendo tutte le variabili che non sono state visitate
    occ_compl = []  # variabili del complemento
    for v in var_compl:
        for occ in find_occurencies(tree, v):
            occ_compl.append(occ)
            # il complemento comparirà sia in subj che in compl (xke è una funzione del tipo f(x,y))
            # occorre rimuoverla da subj
            if occ in mod_subj:
                mod_subj.remove(occ)

    id = 0
    id, root = create_node(id, type="clause", parent=None, prop={"tense": verb['tns']})

    # soggetto
    id, child_subj = create_node(id, type="subj", parent=root)
    id, child2 = create_node(id, type="spec", parent=child_subj, label="un")
    id, child3 = create_node(id, type="noum", parent=child_subj, label=translate_word(subj['pred']))
    for x in mod_subj:
        id, child = create_node(id, type="modifier", parent=child_subj, label=translate_word(x['pred']))

    # verbo
    id, child_verb = create_node(id, type="verb", parent=root, label=translate_word(verb['pred']))

    # complemento
    id, child_compl = create_node(id, type="complement", parent=root)

    for x in occ_compl:
        if x['tag'] == 'PRP':
            id, child = create_node(id, type="prep", parent=child_compl, label=translate_word(x['pred']))
            occ_compl.remove(x)

    # NP complemento
    id, child_np = create_node(id, type="ppcompl", parent=child_compl)
    for x in occ_compl:
        if x['tag'] == 'N':
            id, child = create_node(id, type="noum", parent=child_np, label=translate_word(x['pred']),
                                    prop={"gen": subj['gen']})
            id, child_p = create_node(id, type="spec", parent=child_np, label="il")
            occ_compl.remove(x)

    for x in occ_compl:
        if x['tag'] == 'JJ':
            id, child = create_node(id, type="modifier", parent=child_np, label=translate_word(x['pred']))
            occ_compl.remove(x)

    return root


def sentence_02(tree):
    """
        FRASE DEL TIPO: exists x.(subj(x), exists e.(VP(e), exists y.(adv(e,y))))
        cioè esiste soggetto, verbo e avverbio che mette in relazione il verbo con qualcosa...
    """

    visited = set()
    # cerchiamo il verbo
    terms = get_semantics(tree)
    var_verb = terms[1 + (len(terms) - 6)]  # quando non ci sono i modificatori, la lista terms è lunga 6
    event = str(var_verb.args[0])
    mod_verb = find_occurencies(tree, event)
    visited.add(event)
    verb = match_pred_pos(tree, var_verb)
    mod_verb.remove(verb)

    # cerchiamo il soggetto
    var_subj = intranstitive_parse(tree, var_verb)
    visited.add(var_subj)
    mod_subj = find_occurencies(tree, var_subj)
    subj = list(filter(lambda x: 'N' == x['tag'], mod_subj))[0]
    mod_subj.remove(subj)

    # cerchiamo il complemento
    var_compl = get_all_variables(tree) - visited
    occ_compl = []  # variabili del complemento
    for v in var_compl:
        for occ in find_occurencies(tree, v):
            occ_compl.append(occ)
            # il complemento comparirà sia in verb che in compl (xke è una funzione del tipo f(x,y))
            # occorre rimuoverla da verb
            if occ in mod_verb:
                mod_verb.remove(occ)

    id = 0
    id, root = create_node(id, type="clause", parent=None, prop={"tense": verb['tns']})

    # soggetto
    id, child_subj = create_node(id, type="subj", parent=root)
    id, child4 = create_node(id, type="spec", parent=child_subj, label="il")
    id, child5 = create_node(id, type="noum", parent=child_subj, label=translate_word(subj['pred']),
                             prop={"gen": subj['gen']})
    for x in mod_subj:
        id, child = create_node(id, type="modifier", parent=child_subj, label=translate_word(x['pred']))

    # verbo e avverbio
    id, child_verb = create_node(id, type="verb", parent=root)
    id, child6 = create_node(id, type="v", parent=child_verb, label=translate_word(verb['pred']))
    for x in mod_verb:
        id, child = create_node(id, type="adv", parent=child_verb, label=translate_word(x['pred']))

    # complemento
    id, child_compl = create_node(id, type="complement", parent=root)
    for x in occ_compl:
        if x['tag'] == 'N':
            if 'loc' in x.keys():
                id, ppcompl = create_node(id, type="ppcompl", parent=child_compl, label=translate_word(x['pred']))
            else:
                id, ppcompl = create_node(id, type="ppcompl", parent=child_compl)
                id, child = create_node(id, type="noum", parent=ppcompl, label=translate_word(x['pred']))
                id, child_p = create_node(id, type="spec", parent=ppcompl, label="il")
            occ_compl.remove(x)
    for x in occ_compl:
        if x['tag'] == 'PRP':
            id, child = create_node(id, type="prep", parent=child_compl, label=translate_word(x['pred']))
            occ_compl.remove(x)

    return root


if __name__ == "__main__":

    argv = sys.argv[1:]
    arg_parser = OptionParser()

    arg_parser.add_option("-i", "--input", help='input file', action="store", type="string", dest="input",
                          default="../input/sentences.txt")

    arg_parser.add_option("-o", "--output", help='output folder', action="store", type="string", dest="output",
                          default="../output/")

    arg_parser.add_option("-g", "--gram", help='grammar file', action="store", type="string", dest="gram",
                          default="../grammars/our_grammar.fcfg")

    (options, args) = arg_parser.parse_args()

    if options.input is None or options.output is None or options.gram is None:
        print("Missing mandatory parameters")
        sys.exit(2)

    sentences = []

    with open(options.input, 'r') as file:
        for line in file:
            sentences.append(line.replace('\n', ''))

    regularExpr = [
        'exists\\s\\w+.\\(\\w+\\(\\w+\\)\\s\\&\\s(\\w+\\(\\w+\\)\\s&\\s)*\\w+\\(\\w+,\\w+\\)\\)',
        'exists\\s\\w+.\\(exists\\s\\w+.\\(\\w+\\(\\w+\\)\\s&\\s\\w+\\(\\w+,\\w+\\)\\)\\s&\\sexists\\s\\w+.\\((\\w+\\(\\w+\\)\\s&\\s)*\\w+\\(\\w+\\)\\s&\\s\\w+\\(\\w+\\)\\s&\\s\\w+\\(\\w+,\\w+\\)\\)\\)',
        'exists\\s\\w+.\\((\\w+\\(\\w+\\)\\s&\\s)*\\w+\\(\\w+\\)\\s&\\sexists\\s\\w+.\\(\\w+\\(\\w+\\)\\s&\\s\\w+\\(\\w+,\\w+\\)\\s&\\s\\w+\\(\\w+\\)\\s&\\sexists\\s\\w+.\\(\\w+\\(\\w+,\\w+\\)\\s&\\s\\w+\\(\\w+\\)\\)\\)\\)'
    ]

    sentences = list(map(lambda x: x.lower(), sentences))

    for index in range(len(sentences)):
        sentence = sentences[index]
        final_tree = None
        trees = parser(sentence, options.gram)

        tree = best_tree(trees)
        semantic = (str(tree.label()['SEM']))

        k = 0
        for i in range(len(regularExpr)):
            if re.match(regularExpr[i], semantic):
                k = i
                break

        print("Match Found! RegExpr number " + str(k))
        print(semantic)

        out = {}
        features = {}
        visited = set()

        if k == 0:
            root = sentence_00(tree)

        elif k == 1:
            root = sentence_01(tree)

        elif k == 2:
            root = sentence_02(tree)

        exporter = JsonExporter(indent=2, sort_keys=True)
        with open(options.output + 'sentence' + str(index) + '.json', 'w') as file:
            exporter.write(root, file)
