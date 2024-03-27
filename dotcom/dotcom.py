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

    def _parse_params(self, query):
        results = re.findall("^[a-zA-Z0-9_-]+=[a-zA-Z0-9%._-]+(&[a-zA-Z0-9_-]+=[a-zA-Z0-9%._-]+)*$", query)

        if results == []:
            return {}

        params = query.split("&")
        queryParams = dict()

        for param in params:
            [key, value] = param.split("=")
            queryParams[key] = value
        
        return queryParams

    async def _execute(self, module, method, receive, params):

        req = { "params": params }

        if method == "POST":
            body  = await receive()
            body = body["body"].decode('utf-8')
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
        params = self._parse_params(scope["query_string"].decode('utf-8'))

        response = ""    

        try:
            complete_path = BASE_FILEPATH + path + "/route.py"

            # WORKS FOR ROUTE.PY IN A GIVEN FOLDER
            if  os.path.exists(complete_path):
                complete_path = complete_path.replace("/", ".").replace(".py", "")[2:]
                module = import_module(complete_path)
                response = await self._execute(module, method, receive, params)

            # CHECK FOR DYNAMIC ROUTING
            else:
                possible_paths = glob(os.path.join(BASE_FILEPATH, "**", r"route.py"), recursive=True)
                for possible_path in possible_paths:
                    if len(possible_path.split("/")) != len(complete_path.split("/")):
                        continue
                    else:
                        path = re.findall(r"\[[a-z]+\]", possible_path)
                        if len(path) == 1:
                            index = possible_path.find(path[0])
                            if possible_path[:index] == complete_path[:index]:
                                possible_path = possible_path.replace("/", ".").replace(".py", "")[2:]
                                module = import_module(possible_path)
                                response = await self._execute(module, method, receive, params)
                                print(path[0][1:-1], complete_path[index: complete_path.find("/", index)])

        except Exception as e:
            print("error", e)

        await send({
        'type': 'http.response.start',
        'status': 200,
        'headers': [
            [b'content-type', b'text/plain'],
        ],
        })

        await send({
            'type': 'http.response.body',
            'body': response.encode('utf-8'),
        })
