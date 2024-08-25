from textblob import TextBlob

test_text = """Choline is a water-soluble substance that is not classified as a 
vitamin because it can be synthesized by the body. However, the 
synthesis of choline is limited and therefore it is recognized as an 
essential nutrient. Choline is need to perform functions such as 
the synthesis of neurotransmitter acetylcholine, the synthesis of 
phospholipids used to make cell membranes, lipid transport, and 
also homocysteine metabolism. A deficiency in choline may lead to 
interfered brain development in the fetus during pregnancy, and in 
adults cause fatty liver and muscle damage. """

# blob = TextBlob(test_text)
# print(blob.tags)
# print(blob.noun_phrases)


import spacy
import pytextrank


# load a spaCy model, depending on language, scale, etc.
nlp = spacy.load("en_core_web_sm")

# add PyTextRank to the spaCy pipeline
nlp.add_pipe("textrank")
doc = nlp(test_text)

# examine the top-ranked phrases in the document
for phrase in doc._.phrases[:10]:
    print(phrase.text.lower())
    
