class Posting:
    # Change from tf to tfidf once we do that for M1 just gonna use tf
    def __init__(self, docid: int, tf: int, fields):
        self.posting_data = {
            'docid': docid,
            'tf': tf,
            'fields': fields
        }

    def __getitem__(self, key):
        """Allow access to dictionary items directly."""
        return self.posting_data[key]

    def __setitem__(self, key, value):
        """Allow setting dictionary items directly."""
        self.posting_data[key] = value