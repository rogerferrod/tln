/*
    CLASSE DI TEST PER INIZIARE AD USARE SIMPLENLG!
 */


import simplenlg.features.Feature;
import simplenlg.features.Tense;
import simplenlg.framework.NLGFactory;
import simplenlg.lexicon.Lexicon;
import simplenlg.lexicon.italian.ITXMLLexicon;
import simplenlg.phrasespec.PPPhraseSpec;
import simplenlg.phrasespec.SPhraseSpec;
import simplenlg.realiser.Realiser;
import simplenlg.phrasespec.NPPhraseSpec;
import simplenlg.features.NumberAgreement;
import simplenlg.framework.*;
import simplenlg.phrasespec.*;
import simplenlg.features.LexicalFeature;
import simplenlg.features.Gender;

//importo feature italiane


public class OurTest {

    public static void main(String[] args) {
        Lexicon italianLexicon = new ITXMLLexicon();
        NLGFactory italianFactory = new NLGFactory(italianLexicon);

        //realiser.setDebugMode(true);
        Realiser realiser = new Realiser();
        String output;

        //SPhraseSpec clauseIt = italianFactory.createClause("tu", "immaginare");
        SPhraseSpec clauseIt = italianFactory.createClause();
        clauseIt.setSubject("tu");
        clauseIt.setVerb("immaginare");
        //NPPhraseSpec object = italianFactory.createNounPhrase("il", "cosa");
        NPPhraseSpec object = italianFactory.createNounPhrase();
        object.setSpecifier("il");
        object.setNoun("cosa");
        object.setFeature(Feature.NUMBER, NumberAgreement.PLURAL);
        clauseIt.setObject(object);
        clauseIt.setFeature(Feature.PROGRESSIVE, true);
        clauseIt.setFeature(Feature.PERFECT, false);
        clauseIt.setFeature(Feature.TENSE, Tense.PRESENT);
        output = realiser.realiseSentence(clauseIt);
        System.out.println(output);


        NPPhraseSpec np_subj = italianFactory.createNounPhrase("un", "taglia");
        clauseIt = italianFactory.createClause(np_subj, "esiste");
        clauseIt.setFeature(Feature.TENSE, Tense.PRESENT);
        NPPhraseSpec np = italianFactory.createNounPhrase("il", "testa");
        np.addModifier("mio");
        //PPPhraseSpec pp = italianFactory.createPrepositionPhrase("sopra", np);
        PPPhraseSpec pp = italianFactory.createPrepositionPhrase();
        pp.setPreposition("sopra");
        pp.setComplement(np);
        clauseIt.addComplement(pp);
        output = realiser.realiseSentence(clauseIt);
        System.out.println(output);


        WordElement noum = italianLexicon.getWord("opportunità", LexicalCategory.NOUN);  //non c'è nel lessico
        noum.setFeature(LexicalFeature.GENDER, Gender.FEMININE);
        NPPhraseSpec subj = italianFactory.createNounPhrase("il", noum);
        subj.addModifier("tuo");
        subj.addModifier("grade");
        VPPhraseSpec verb = italianFactory.createVerbPhrase("volare");
        verb.addComplement("via");
        clauseIt = italianFactory.createClause(subj, verb);
        /*clauseIt.setFeature(Feature.PROGRESSIVE, true);
        clauseIt.setFeature(Feature.PERFECT, false);
        clauseIt.setFeature(Feature.TENSE, Tense.PRESENT);*/
        verb.setFeature(Feature.PROGRESSIVE, true);
        verb.setFeature(Feature.PERFECT, false);
        verb.setFeature(Feature.TENSE, Tense.PRESENT);
        PPPhraseSpec pp2 = italianFactory.createPrepositionPhrase("da", "qui");
        clauseIt.addComplement(pp2);
        output = realiser.realiseSentence(clauseIt);
        System.out.println(output);
    }
}
