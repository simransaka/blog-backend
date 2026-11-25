from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from api.routes import chat as chat_routes
from src.database import MarkdownFile


class FakeQuery:
    def __init__(self, result):
        self.result = result
        self.filters = ()

    def filter(self, *criteria):
        self.filters = criteria
        return self

    def order_by(self, _ordering):
        return self

    def all(self):
        return self.result

    def first(self):
        return self.result


class FakeDatabase:
    def __init__(self, result):
        self.query_result = FakeQuery(result)

    def query(self, _model):
        return self.query_result


def test_document_list_is_scoped_to_current_user():
    document = SimpleNamespace(id="file-1", title="A blog", version=1)
    db = FakeDatabase([document])

    result = chat_routes.get_chat_documents(
        db=db,
        current_user=SimpleNamespace(id=27),
    )

    assert result == [{"id": "file-1", "title": "A blog", "version": 1}]
    user_filter = next(
        criterion
        for criterion in db.query_result.filters
        if criterion.left.name == "user_id"
    )
    assert user_filter.right.value == 27


def test_chat_rejects_files_not_owned_by_current_user():
    db = FakeDatabase(None)

    with pytest.raises(HTTPException) as exc_info:
        chat_routes.chat(
            request=chat_routes.ChatRequest(
                file_id="another-users-file",
                question="What is this about?",
            ),
            db=db,
            current_user=SimpleNamespace(id=27),
        )

    assert exc_info.value.status_code == 404
    assert any(
        criterion.left.name == "user_id"
        and criterion.right.value == 27
        for criterion in db.query_result.filters
    )


def test_chat_retrieves_only_the_owned_file_version(monkeypatch):
    document = SimpleNamespace(id="file-1", version=3)
    db = FakeDatabase(document)
    service_call = {}

    def fake_chat_with_markdowns(**kwargs):
        service_call.update(kwargs)
        return {"answer": "Answer", "sources": []}

    monkeypatch.setattr(
        chat_routes,
        "chat_with_markdowns",
        fake_chat_with_markdowns,
    )

    result = chat_routes.chat(
        request=chat_routes.ChatRequest(
            file_id="file-1",
            question="What is this about?",
        ),
        db=db,
        current_user=SimpleNamespace(id=27),
    )

    assert result == {"answer": "Answer", "sources": []}
    assert service_call == {
        "question": "What is this about?",
        "file_id": "file-1",
        "version": 3,
        "top_k": 4,
    }
