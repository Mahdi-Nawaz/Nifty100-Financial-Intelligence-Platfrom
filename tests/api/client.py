"""Lightweight, deterministic API test client avoiding AnyIO portal thread deadlocks on Windows."""
import urllib.parse
import inspect
from typing import get_origin, get_args, Union
from fastapi import HTTPException
from fastapi.responses import JSONResponse, FileResponse
from src.api.main import app

class APIResponse:
    def __init__(self, status_code: int, data: any):
        self.status_code = status_code
        self._data = data

    def json(self):
        return self._data

class DirectAPIClient:
    """Dispatches HTTP GET requests directly to FastAPI route handlers."""
    def __init__(self, fastapi_app):
        self.app = fastapi_app

    def get(self, url: str) -> APIResponse:
        parsed = urllib.parse.urlparse(url)
        path = parsed.path
        qs = urllib.parse.parse_qs(parsed.query)
        query_params = {k: v[0] for k, v in qs.items()}

        for route in self.app.routes:
            if hasattr(route, 'path_regex'):
                match = route.path_regex.match(path)
                if match and 'GET' in route.methods:
                    path_params = match.groupdict()
                    all_params = {**query_params, **path_params}
                    try:
                        sig = inspect.signature(route.endpoint)
                        call_kwargs = {}
                        for p_name, param in sig.parameters.items():
                            if p_name in all_params:
                                raw_val = all_params[p_name]
                                target_type = param.annotation
                                # Unpack typing.Optional
                                if get_origin(target_type) is Union:
                                    args = [a for a in get_args(target_type) if a is not type(None)]
                                    if args:
                                        target_type = args[0]

                                if target_type is int:
                                    call_kwargs[p_name] = int(raw_val)
                                elif target_type is float:
                                    call_kwargs[p_name] = float(raw_val)
                                else:
                                    call_kwargs[p_name] = raw_val

                        res = route.endpoint(**call_kwargs)
                        if isinstance(res, (JSONResponse, FileResponse)):
                            status = res.status_code
                            data = res.body if hasattr(res, 'body') else {}
                        else:
                            status = 200
                            data = res
                        return APIResponse(status, data)
                    except HTTPException as e:
                        return APIResponse(e.status_code, {'detail': e.detail})
                    except Exception as e:
                        return APIResponse(500, {'detail': str(e)})

        return APIResponse(404, {'detail': f'Not Found: {path}'})

client = DirectAPIClient(app)
