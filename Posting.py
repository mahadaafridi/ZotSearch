class Posting:
    # Change from tf to tfidf once we do that for M1 just gonna use tf
    def __init__(self, docid: int, tf: int, fields):
        self.docid = docid # Document ID
        self.tf = tf # Term Frequency
        self.fields = fields # title, header, strong, body fields