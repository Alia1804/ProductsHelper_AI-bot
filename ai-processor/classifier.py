import spacy
import pickle
from vectorizer import Vectorizer

MODEL_PATH = './models/logistic_regression_model.pkl'


class Classifier:
    def __init__(self, vectorizer: Vectorizer):
        self.vectorizer = vectorizer
        self.nlp = spacy.load("ru_core_news_lg")
        self.model = pickle.load(open(MODEL_PATH, 'rb'))

    def get_ents(self, text: str):
        doc = self.nlp(text)
        spans = []
        
        for token in doc:
            if token.pos_ == "NOUN":
                subtree = list(token.subtree)
                start = min(t.i for t in subtree)
                end = max(t.i for t in subtree) + 1
                span = doc[start:end]
                
                if len(span) <= 6:
                    spans.append(span)
        
        spans = sorted(spans, key=lambda x: -len(x))
        
        filtered_spans = []
        for span in spans:
            if not any(
                (span.start >= existing.start and span.end <= existing.end)
                for existing in filtered_spans
            ):
                filtered_spans.append(span)
        
        return [span.text for span in filtered_spans]


    
    def preprocess(self, text: str):

        doc = self.nlp(text.lower())
        intent_tokens = []

        allowed_pos = {"VERB", "PRON", "PART", "ADV", "CCONJ", "ADP"}

        for token in doc:
            if token.pos_ in allowed_pos and not token.is_stop and not token.is_punct and not token.is_space:
                intent_tokens.append(token.lemma_)

        return " ".join(intent_tokens)

    def get_class(self, text):
        preprocessed = self.preprocess(text)
        emb = self.vectorizer.generate_embedding(preprocessed).reshape(1, -1)
        return int(self.model.predict(emb)[0])
