from __future__ import annotations

from typing import IO, List, Union
import typing as t
from io import BytesIO

from starlette.requests import Request
from multipart.multipart import parse_options_header
from starlette.datastructures import UploadFile

from bentoml.exceptions import BentoMLException
from bentoml._internal.types import FileLike
from bentoml.io import File

class WSIFile(File):
   

    def __new__(  # pylint: disable=arguments-differ # returning subclass from new
        cls, kind = "binaryio", mime_type: str | None = None
    ) -> File:
        mime_type = mime_type if mime_type is not None else "application/octet-stream"

        if kind == "binaryio":
            res = object.__new__(BytesIOFile)
        else:
            raise ValueError(f"invalid File kind '{kind}'")

        res._mime_type = mime_type
        return res

class BytesIOFile(File):
    async def from_http_request(self, request: Request) -> IO[bytes]:
        # return request
        content_type, _ = parse_options_header(request.headers["content-type"])
        if content_type.decode("utf-8") == "multipart/form-data":
            form = await request.form()
            found_mimes: List[str] = []
            val: Union[str, UploadFile]
            for val in form.values():  # type: ignore
                if isinstance(val, UploadFile):
                    found_mimes.append(val.content_type)  # type: ignore (bad starlette types)
                    if val.content_type == self._mime_type:  # type: ignore (bad starlette types)
                        res = FileLike[bytes](val.file, val.filename)  # type: ignore (bad starlette types)
                        break
                    if 'image/' in val.content_type:
                        res = FileLike[bytes](val.file, val.filename)  # type: ignore (bad starlette types)
                        break
            else:
                if len(found_mimes) == 0:
                    raise BentoMLException("no File found in multipart form")
                else:
                    raise BentoMLException(
                        f"multipart File should have Content-Type '{self._mime_type}', got files with content types {', '.join(found_mimes)}"
                    )
            return res  # type: ignore
        body = await request.body()
        return t.cast(IO[bytes], FileLike(BytesIO(body), "<request body>"))

