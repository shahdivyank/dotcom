import json


class Response:
    def __init__(self, status=500, data="nothing"):
        self.response = {"status": status, "data": data}

    def parse_response(self):
        return json.dumps(self.response)

    def json(self, data=""):
        self.response.update({"data": data})
        return self

    def status(self, status):
        self.response.update({"status": status})
        return self
