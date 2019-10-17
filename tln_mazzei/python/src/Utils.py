import re


def best_tree(trees):
    """
    Data una lista di alberi, ritorna quello corretto, cioè quello senza lambda-espressioni nella radice
    :param trees: lista di alberi
    :return: l'albero corretto
    """
    final_tree = None
    for tree in trees:
        flag = True
        s = tree.label()['SEM']
        stri = str(s)
        stri_split = stri.split()
        for k in stri_split:
            if "\\" in k:
                flag = False

        if not flag:
            continue

        variables = get_all_variables(tree)
        terms = list(subterms(tree.label()['SEM'].term))
        terms = list(map(lambda x: x.pred.variable.name, terms))
        for v in variables:
            if terms.__contains__(v):
                flag = False

        if flag:
            final_tree = tree
    return final_tree


def get_semantics(tree):
    """
    :param tree: albero in input
    :return: tutti i termini della semantica
    """
    return subterms(tree.label()['SEM'].term)


def get_all_variables(tree):
    """
    :param tree: albero
    :return: insieme di variabili all'interno di un albero
    """
    terms = list(subterms(tree.label()['SEM'].term))
    variables = set()
    for t in terms:
        for a in t.args:
            variables.add(a.variable.name)

    return variables


def find_occurencies(tree, var):
    """
    Ritorna tutte le occorrenze all'interno della semantica di una certa variabile (senza prestare attenzione allo scope)
    :param tree: albero
    :param var: variabile da cercare
    :return: lista di foglie contenenti la variabile var
    """
    res = []
    terms = find_sem_occurencies(tree, var)
    for t in terms:
        node = match_pred_pos(tree, t)
        if node is not None and not res.__contains__(node):
            res.append(node)

    return res


def find_sem_occurencies(tree, var):
    """
    Metodo ausiliario al metodo find_occurencies
    :param tree: albero
    :param var: variabile da cercare
    :return: lista di nodi contenenti la variabile var
    """
    res = set()
    term = tree.label()['SEM'].term
    terms = subterms(term)
    for t in terms:
        args = get_term_arguments(t)
        if var in args:
            res.add(t)
    return list(res)  # ritorna nodi


def transtitive_parse(verb):
    """
    :param verb: verbo transitivo
    :return: gli argomenti del verbo
    """
    return get_arguments(verb)


def intranstitive_parse(tree, verb):
    """
    :param tree: albero, bisogna passarlo perchè in un verbo intransitivo bisogna cercare il soggetto altrove
    :param verb: verbo intransitivo
    :return: la variabile che indica il soggetto
    """
    terms = subterms(tree.label()['SEM'].term)
    agent = list(filter(lambda x: x.pred.variable.name == 'agent', terms))[0]
    subj = agent.args[1].variable.name
    return subj


def subterms(term):
    """
    :param term: termine in input
    :return: ritorna tutti i termini di cui è composto term
    """
    terms = []
    aux_subterms(term, terms)
    return terms


def aux_subterms(term, terms):
    # serie di if per differenziare la composizione dell'albero
    if hasattr(term, 'term'):
        aux_subterms(term.term, terms)
    if hasattr(term, 'first'):
        aux_subterms(term.first, terms)
    if hasattr(term, 'second'):
        aux_subterms(term.second, terms)
    elif hasattr(term, 'pred'):
        if not terms.__contains__(term):  # preserva l'ordine
            terms.append(term)  # foglia


def get_arguments(node):
    # ritorna gli argomenti di un nodo
    return list(map(lambda x: x.variable.name, node.args))


def get_term_arguments(term):
    # ritorna gli argomenti di un termine
    l = term.args
    return list(map(lambda x: x.variable.name, l))


def match_pred_pos(tree, term):
    """
    match tra termine semantico e PoS-Tag
    :param tree: albero
    :param term: termine semantico
    :return: nodo con l'informazione del PoS-Tag
    """
    leaves = ['TV', 'IV', 'DTV', 'N', 'JJ', 'PropN', 'Det', 'EX', 'PRP', 'AUX', 'CP', 'ADV']
    pred_name = term.pred.variable.name if hasattr(term, 'pred') else term

    terminals = [i for i in tree.subtrees()]  # ritorna tutti i possibili sottoalberi
    terminals = list(
        filter(lambda x: re.search("\\'(.*)\\'", str(x.label()).split('\n')[0], re.IGNORECASE).group(1) in leaves,
               terminals))  # adesso in subtrees avrò solo le foglie

    # aggiunge tutte le informazioni
    for t in terminals:
        if pred_name == get_lemma(t):
            tag = re.search("\\'(.*)\\'", str(t.label()).split('\n')[0], re.IGNORECASE).group(1)
            node = {'pred': pred_name, 'tag': tag}
            # in base a quali features ci sono all'interno del nodo dell'albero
            if 'NUM' in t.label().keys():
                node['num'] = t.label()['NUM']
            if 'TNS' in t.label().keys():
                node['tns'] = t.label()['TNS']
            if tag in ['N', 'PropN'] and 'GEN' in t.label().keys():
                node['gen'] = t.label()['GEN']
            if 'LOC' in t.label().keys():
                node['loc'] = True
            return node
    return None


def get_lemma(term):
    # esempio: dato image(x,y) ritorna image
    tag = re.search("\\'(.*)\\'", str(term.label()).split('\n')[0], re.IGNORECASE).group(1)
    if tag == 'TV':
        term = term.label()['SEM'].term
        terms = subterms(term)
        terms = list(map(lambda x: x.argument.term, terms))
    elif tag == 'PRP' and 'PERS' in term.label().keys():
        term = term.label()['SEM'].term
        return term.argument.variable.name
    elif tag == 'PRP' and 'LOC' in term.label().keys():
        term = subterms(term.label()['SEM'].term)[0]
        return term.argument.term.second.pred.variable.name
    elif tag == 'PropN':
        return term.label()['SEM'].term.argument.variable.name
    else:
        term = term.label()['SEM'].term
        terms = subterms(term)
    terms = list(map(lambda x: x.pred.variable.name, terms))
    return terms[0] if len(terms) > 0 else None
