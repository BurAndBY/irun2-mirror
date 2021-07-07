class StatementRepresentation(object):
    def __init__(self, problem):
        self.problem = problem
        self.attachment_name = None
        self.iframe_name = None
        self.content = None
        self.lang_selector = None

    @property
    def is_empty(self):
        return self.attachment_name is None and self.iframe_name is None and self.content is None
