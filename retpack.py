from typing import Any


def ok(data: Any = None, code: int = 0, message: str = "OK"):
    return {"code": code, "message": message, "data": data}


def fail(code: int, message: str):
    return {"code": code, "message": message}
