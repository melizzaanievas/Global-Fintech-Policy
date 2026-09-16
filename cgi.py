"""Minimal compatibility shim for packages that still import the removed stdlib `cgi` module."""

from email.message import Message
from html import escape as _html_escape
from urllib.parse import parse_qs, parse_qsl

__all__ = ["escape", "parse_header", "parse_qs", "parse_qsl"]


def escape(s, quote=False):
    return _html_escape(s, quote=quote)


def parse_header(line):
    if not line:
        return "", {}

    message = Message()
    message["content-type"] = str(line)
    params = message.get_params(header="content-type", unquote=True) or []
    if not params:
        return str(line).strip(), {}

    value = params[0][0]
    options = {key: val for key, val in params[1:] if key}
    return value, options
