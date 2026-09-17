from __future__ import annotations

import pytest

from derive_surface import api


class Resp:
    def __init__(self, status, payload=None, bad_json=False):
        self.status_code, self.payload, self.bad_json = status, payload, bad_json

    def json(self):
        if self.bad_json:
            raise ValueError("Expecting value: line 2 column 1 (char 1)")
        return self.payload


class Session:
    def __init__(self, responses):
        self.responses = list(responses)
        self.posts = 0

    def post(self, url, json, timeout):
        self.posts += 1
        return self.responses.pop(0)


def test_call_retries_on_unparseable_body(monkeypatch):
    monkeypatch.setattr(api.time, "sleep", lambda s: None)
    sess = Session([Resp(200, bad_json=True), Resp(200, {"result": 42})])
    assert api.DeriveClient(session=sess, max_retries=3).call("get_time") == 42
    assert sess.posts == 2


def test_call_gives_up_after_max_retries(monkeypatch):
    monkeypatch.setattr(api.time, "sleep", lambda s: None)
    sess = Session([Resp(200, bad_json=True)] * 3)
    with pytest.raises(RuntimeError, match="giving up"):
        api.DeriveClient(session=sess, max_retries=3).call("get_time")
