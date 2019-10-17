import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import simplenlg.features.Feature;
import simplenlg.features.Gender;
import simplenlg.features.LexicalFeature;
import simplenlg.features.NumberAgreement;
import simplenlg.framework.NLGFactory;
import simplenlg.lexicon.Lexicon;
import simplenlg.lexicon.italian.ITXMLLexicon;
import simplenlg.phrasespec.NPPhraseSpec;
import simplenlg.phrasespec.PPPhraseSpec;
import simplenlg.phrasespec.SPhraseSpec;
import simplenlg.phrasespec.VPPhraseSpec;
import simplenlg.realiser.Realiser;

import java.io.IOException;
import java.util.HashMap;

public class NLGtree {

    private HashMap<Integer, HashMap<String, String>> treeHash = new HashMap<>();
    private HashMap<Integer, NPPhraseSpec> hashNP = new HashMap<>();
    private HashMap<Integer, PPPhraseSpec> hashPP = new HashMap<>();
    private HashMap<Integer, VPPhraseSpec> hashVP = new HashMap<>();
    private Lexicon italianLexicon = new ITXMLLexicon();
    private NLGFactory italianFactory = new NLGFactory(italianLexicon);


    public NLGtree(String sentence) {
        ObjectMapper objectMapper = new ObjectMapper();
        try {
            JsonNode root = objectMapper.readTree(sentence);
            visit(root, null);
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    public String getRealisedSentence() {
        SPhraseSpec clauseIt = italianFactory.createClause();

        fillTree(clauseIt, 2);

        String features = treeHash.get(1).get("features");
        if (parseFeatures(features).get("tense").equals("ger")) {
            clauseIt.setFeature(Feature.PROGRESSIVE, true);
            clauseIt.setFeature(Feature.PERFECT, false);
        }

        Realiser realiser = new Realiser();
        return realiser.realiseSentence(clauseIt);
    }

    /**
     *
     * @param features stringa associata al dizionario pyhton
     * @return parsifica la stringa (dizionario python) e la converte in un HashMap
     */
    private HashMap<String, String> parseFeatures(String features) {
        HashMap<String, String> map = new HashMap<>();

        features = features.replace("\"", "");
        features = features.replace("'", "");
        features = features.replace("{", "");
        features = features.replace("}", "");
        String splits[] = features.split(",");
        for (String tuple : splits) {
            String parsed[] = tuple.split(":");
            map.put(parsed[0], parsed[1].trim());
        }

        return map;
    }

    private void fillTree(SPhraseSpec clauseIt, int key) {
        if (!treeHash.keySet().contains(key)) {
            // fine ricorsione
            return;
        }

        HashMap<String, String> node = treeHash.get(key);

        if (!node.keySet().contains("label")) {
            /* se non ha "label" vuol dire che è un nodo -> serve creare un nodo
             * il tipo del nodo dipende da "type"
             * memorizziamo il nodo in un HashMap in modo da accedervi facilmente
             * la scelta del HasMap dipende dal tipo
             * abbiamo 3 HashMap diversi (NP, VP, PP) perchè i nodi hanno tipi diversi con metodi specifici
             * non si può sfruttare ereditarietà e polimorfismo
             */

            // in base al tipo di nodo, creiamo il costituente associato
            switch (node.get("type")) {
                case "obj": {
                    NPPhraseSpec np = italianFactory.createNounPhrase();
                    hashNP.put(key, np);
                    clauseIt.setObject(np); // per semplicità assumiamo che si attacchi sempre e solo a clause
                    /*
                    //altrimenti bisognerebbe cercarlo...
                    NPPhraseSpec parent = getNPParent(node);
                    if(parent != null)
                    //poi prova con PP
                    */

                    break;
                }
                case "subj": {
                    NPPhraseSpec np = italianFactory.createNounPhrase();
                    hashNP.put(key, np);
                    clauseIt.setSubject(np); // per semplicità si attacca solo a clause
                    break;
                }
                case "complement":
                    PPPhraseSpec pp = italianFactory.createPrepositionPhrase();
                    hashPP.put(key, pp);
                    clauseIt.addComplement(pp); // per semplicità si attacca solo a clause (non abbiamo PP innestati)
                    break;
                case "ppcompl": {
                    NPPhraseSpec np = italianFactory.createNounPhrase();
                    hashNP.put(key, np);
                    getPPParent(node).setComplement(np); //il padre sarà per forza un PP
                    break;
                }
                case "verb":
                    VPPhraseSpec vp = italianFactory.createVerbPhrase();
                    hashVP.put(key, vp);
                    clauseIt.setVerb(vp); //il padre sarà per forza una clause
                    break;
            }
        } else {
            // aggiunge i figli ai nodi (esempio: aggiunge lo spec ad un oggetto)
            // i primi 3 si attaccano solo a clause (ipotesi semplificativa)
            switch (node.get("type")) {
                case "subj":
                    clauseIt.setSubject(node.get("label"));
                    break;
                case "obj":
                    clauseIt.setObject(node.get("label"));
                    break;
                case "verb":
                    clauseIt.setVerb(node.get("label"));
                    break;
                case "spec":
                    getNPParent(node).setSpecifier(node.get("label")); //spec fa parte di un NP
                    break;
                case "noum":
                    getNPParent(node).setNoun(node.get("label")); //noum fa parte di un NP
                    String features = node.get("features");
                    if (features != null) {
                        String number = parseFeatures(features).get("number");
                        String genre = parseFeatures(features).get("gen");
                        if (number != null) {
                            getNPParent(node).setFeature(Feature.NUMBER, (number.equals("pl")) ? NumberAgreement.PLURAL : NumberAgreement.SINGULAR);
                        }
                        if (genre != null) {
                            getNPParent(node).setFeature(Feature.NUMBER, (genre.equals("pl")) ? NumberAgreement.PLURAL : NumberAgreement.SINGULAR);
                            getNPParent(node).setFeature(LexicalFeature.GENDER, (genre.equals("f")) ? Gender.FEMININE : Gender.MASCULINE);
                        }
                    }
                    break;
                case "prep":
                    getPPParent(node).setPreposition(node.get("label")); //prep fa parte di un PP
                    break;
                case "ppcompl":
                    getPPParent(node).setComplement(node.get("label")); //ppcompl fa parte di un PP
                    break;
                case "modifier":
                    getNPParent(node).addModifier(node.get("label")); //modifier fa parte di un NP
                    break;
                case "v":
                    getVPParent(node).setVerb(node.get("label")); //v fa parte di un VP
                    break;
                case "adv":
                    getVPParent(node).addComplement(node.get("label")); //adv fa parte di un VP
                    break;
            }
        }

        fillTree(clauseIt, ++key);
    }

    // i prossimi tre metodi si differenziano per tipo di ritorno
    private NPPhraseSpec getNPParent(HashMap<String, String> node) {
        int parent = Integer.parseInt(node.get("parent"));
        return hashNP.get(parent);
    }

    private PPPhraseSpec getPPParent(HashMap<String, String> node) {
        int parent = Integer.parseInt(node.get("parent"));
        return hashPP.get(parent);
    }

    private VPPhraseSpec getVPParent(HashMap<String, String> node) {
        int parent = Integer.parseInt(node.get("parent"));
        return hashVP.get(parent);
    }

    // metodo ricorsivo per la parsificazione della stringa JSON creata da Python
    private void visit(JsonNode jsonNode, JsonNode jsonNodeParent) {
        HashMap<String, String> nodeHash = new HashMap<>();
        nodeHash.put("parent", (jsonNodeParent != null) ? jsonNodeParent.get("a").asText() : "null");
        nodeHash.put("type", jsonNode.get("b").asText());
        if (jsonNode.get("c") != null) {
            nodeHash.put("label", jsonNode.get("c").asText());
        }

        if (jsonNode.get("d") != null) {
            nodeHash.put("features", jsonNode.get("d").toString());
        }

        treeHash.put(jsonNode.get("a").asInt(), nodeHash);

        ArrayNode arrayNode = (ArrayNode) jsonNode.get("children");
        if (arrayNode == null) {
            return;
        }
        for (int i = 0; i < arrayNode.size(); i++) {
            visit(arrayNode.get(i), jsonNode);
        }
    }
}

