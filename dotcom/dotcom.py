import os
import re
from importlib import import_module
from glob import glob
from dotenv import load_dotenv
import json
from inspect import signature

BASE_FILEPATH = "./api"


class Dotcom:

    def __init__(self):
        load_dotenv()

    def _parse_query(self, query):
        results = re.findall(
            "^[a-zA-Z0-9_-]+=[a-zA-Z0-9%._-]+(&[a-zA-Z0-9_-]+=[a-zA-Z0-9%._-]+)*$",
            query,
        )

        if results == []:
            return {}

        params = query.split("&")
        queryParams = dict()

        for param in params:
            [key, value] = param.split("=")
            queryParams[key] = value

        return queryParams

    def _parse_params(self, route, filepath):
        params = dict()

        split_filepath = filepath.split("/")
        split_route = route.split("/")

        for index in range(len(split_filepath)):
            if split_filepath[index] != split_route[index]:
                params[split_filepath[index][1:-1]] = split_route[index]

        return params

    async def _execute(self, module, method, receive, query, params):
        req = {"query": query, "params": params}

        if method == "POST":
            body = await receive()
            body = body["body"].decode("utf-8")
            req["body"] = json.loads(body)

        function = getattr(module, method)
        if len(signature(function).parameters) == 1:
            response = function(req)
        else:
            response = function()

        return response.parse_response()

    async def run(self, scope, receive, send):
        method = scope["method"]
        path = scope["path"]
        query = self._parse_query(scope["query_string"].decode("utf-8"))

        response = ""

        all_possible_routes = glob(
            os.path.join(BASE_FILEPATH, "**", r"route.py"), recursive=True
        )

        for possible_route in all_possible_routes:
            trimmed_route = possible_route[5:-9]
            striped_route = re.sub(
                "\[[A-Za-z0-9_-]+\]", "[A-Za-z0-9_-]+", trimmed_route
            )
            striped_route = "^" + striped_route + "$"
            search = re.match(striped_route, path)

            if search:
                params = self._parse_params(path, trimmed_route)
                route = possible_route.replace("/", ".").replace(".py", "")[2:]
                module = import_module(route)
                response = await self._execute(module, method, receive, query, params)

        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": [
                    [b"content-type", b"text/plain"],
                ],
            }
        )

        await send(
            {
                "type": "http.response.body",
                "body": response.encode("utf-8"),
            }
        )
