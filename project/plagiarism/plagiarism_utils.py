from django.db import connection

class QueryExecutor:
    cursor = connection.cursor()

    def put(self, query, params = None):
    	if params is None:
    		params = []
        self.cursor.execute(query, params)

    def get(self, query, params = None):
    	if params is None:
    		params = []
        self.cursor.execute(query, params)
        return self.cursor.fetchall()
    

    


