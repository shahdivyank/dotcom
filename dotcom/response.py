import json


class Response:
    def __init__(self, status: int = 500, data: str = "nothing") -> None:
        self.response: dict = {"status": status, "data": data}

    def parse_response(self) -> str:
        return json.dumps(self.response)

    def json(self, data: str = ""):
        self.response.update({"data": data})
        print(self, type(self))
        return self

    def status(self, status: int):
        self.response.update({"status": status})
        return self
