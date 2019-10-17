"""
Word Sense Disambiguation
provides an implementation of the lesk algorithm
disambiguate the files given in input
"""

__author__ = 'Davide Giosa, Roger Ferrod, Simone Cullino'

import re
import sys
from optparse import OptionParser
import xml.etree.ElementTree as ET
from lxml import etree as Exml

from src.Esercitazione2.lesk import *


def parse_txt(path):
    """
    Parsifica il testo in input
    Le parole da disambiguare sono racchiuse tra *
    :param path: percorso del file di input (sentences.txt)
    :return: lista di frasi, lista di parole da disambiguare
    """

    sentences_list = []
    words_list = []
    with open(path, 'r') as fileTXT:
        for line in fileTXT.readlines():
            word = re.search('\*\*(.*)\*\*', line, re.IGNORECASE).group(1)
            sentence = re.sub('\*\*(.*)\*\*', word, line)

            sentences_list.append(sentence)
            words_list.append(word)
    return sentences_list, words_list


def parse_xml(path):
    """
    Parsifica SemCor Corpus annotato manualmente sui Synset di WordNet

    1) carico file xml
    2) prendo tutti tag s
    3) ricavo la frase
    4) selezione delle parole da disambiguare (selezionando quelle che servono) con num sensi >=2
    5) ricavo senso annotato (golden) da wsn

    :param path: percorso del file XML (Brown Corpus)
    :return: [(sentence, [(word, gold)])]
    """

    with open(path, 'r') as fileXML:
        data = fileXML.read()

        # correzioni xml non ben formattato
        data = data.replace('\n', '')
        replacer = re.compile("=([\w|:|\-|$|(|)|']*)")
        data = replacer.sub(r'="\1"', data)

        result = []
        try:
            root = Exml.XML(data)
            paragraphs = root.findall("./context/p")
            sentences = []
            for p in paragraphs:
                sentences.extend(p.findall("./s"))
            for sentence in sentences:
                words = sentence.findall('wf')
                sent = ""
                tuple_list = []
                for word in words:
                    w = word.text
                    pos = word.attrib['pos']
                    sent = sent + w + ' '
                    if pos == 'NN' and '_' not in w and len(wn.synsets(w)) > 1 and 'wnsn' in word.attrib:
                        sense = word.attrib['wnsn']
                        t = (w, sense)
                        tuple_list.append(t)
                result.append((sent, tuple_list))
        except Exception as e:
            raise NameError('xml: ' + str(e))
    return result


def main():
    """
    Es2 A
    Disambiguate the polysemic terms within the sentences of the file ‘Sentences.txt’,
    It returns the synset IDs of the appropriate sense for the context
    Writes the output into a txt file
    """

    list_sentences, list_words = parse_txt(options.input1)
    with open(options.output + 'Es2A.txt', "w") as out:
        out.write('Word,   Synset ID,   Synonyms,    Definition\n')
        for i in range(len(list_sentences)):
            amb_word = list_words[i]
            sentence = list_sentences[i]
            sense = lesk(amb_word, sentence)
            synonyms = find_synonims(sense)
            out.write('{0}, {1}, {2}, {3}\n'.format(amb_word, str(sense), str(synonyms), sense.definition()))

    """
    Es2 B
    Extracts sentences from the SemCor corpus (corpus annotated with WN synset) 
    and disambiguates at least one noun per sentence.
    It also calculates the accuracy based on the senses noted in SemCor.
    Writes the output into a xml file
    """

    list_xml = parse_xml(options.input2)

    result = []
    count_word = 0
    count_exact = 0
    for i in range(len(list_xml)):
        dict_list = []
        sentence = list_xml[i][0]
        words = list_xml[i][1]
        for t in words:
            sense = lesk(t[0], sentence)
            value = str(get_sense_index(t[0], sense))
            golden = t[1]
            count_word += 1
            if golden == value:
                count_exact += 1
            dict_list.append({'word': t[0], 'gold': golden, 'value': value})

        if len(dict_list) > 0:
            result.append((sentence, dict_list))

    accuracy = count_exact / count_word

    with open(options.output + 'Es2B.xml', 'wb') as out:
        out.write('<results accurancy="{0:.2f}">'.format(accuracy).encode())
        for i in range(len(result)):
            xml_s = ET.Element('s')
            xml_s.set('snum', str(i + 1))
            xml_sentence = ET.SubElement(xml_s, 'sentence')
            xml_sentence.text = result[i][0]
            for tword in result[i][1]:
                xml_word = ET.SubElement(xml_sentence, 'word')
                xml_word.text = tword['word']
                xml_word.set('golden', tword['gold'])
                xml_word.set('sense', tword['value'])

            tree = ET.ElementTree(xml_s)
            tree.write(out)

        out.write(b'</results>')


if __name__ == "__main__":
    print('Lesk algorithm')

    argv = sys.argv[1:]
    parser = OptionParser()

    parser.add_option("-a", "--input1", help='first input file', action="store", type="string", dest="input1",
                      default="../../input/sentences.txt")

    parser.add_option("-b", "--input2", help='second input file', action="store", type="string", dest="input2",
                      default="../../input/br-a01.xml")

    parser.add_option("-o", "--output", help='output directory', action="store", type="string", dest="output",
                      default="../../output/Es2/")

    (options, args) = parser.parse_args()

    if options.input1 is None or options.input2 is None:
        print("Missing mandatory parameters")
        sys.exit(2)

    main()

    # sentence = 'I arrived at the bank after crossing the river'
    # sentence = 'I arrived at the bank after crossing the road'
