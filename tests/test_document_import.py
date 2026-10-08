import io
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from .test_http_providers_knowledge import headers


def pdf(pages: int = 1, encrypted: bool = False, text: bool = True) -> bytes:
    writer = PdfWriter()
    for _ in range(pages):
        page = writer.add_blank_page(width=300, height=300)
        if text:
            font = DictionaryObject(
                {
                    NameObject("/Type"): NameObject("/Font"),
                    NameObject("/Subtype"): NameObject("/Type1"),
                    NameObject("/BaseFont"): NameObject("/Helvetica"),
                }
            )
            page[NameObject("/Resources")] = DictionaryObject(
                {NameObject("/Font"): DictionaryObject({NameObject("/F1"): font})}
            )
            stream = DecodedStreamObject()
            stream.set_data(b"BT /F1 12 Tf 30 250 Td (Warranty lasts thirty days.) Tj ET")
            page[NameObject("/Contents")] = stream
    if encrypted:
        writer.encrypt("test-key")
    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def test_text_pdf_is_imported_and_searchable(app: FastAPI) -> None:
    with TestClient(app) as c:
        r = c.post(
            "/api/knowledge/import?name=warranty.pdf",
            headers={**headers(app), "Content-Type": "application/pdf"},
            content=pdf(),
        )
        assert r.status_code == 200
        result = c.get("/api/knowledge/answer?query=warranty", headers=headers(app)).json()
        assert result["status"] == "answered"
        assert result["sources"][0]["id"] == r.json()["id"]


@pytest.mark.parametrize(
    "data,error",
    [
        (b"%PDF-invalid", "document_parse_failed"),
        (pdf(encrypted=True), "encrypted_pdf_unsupported"),
        (pdf(text=False), "scanned_pdf_unsupported"),
        (pdf(pages=2), "pdf_page_limit"),
    ],
)
def test_failed_pdf_does_not_modify_knowledge(app: FastAPI, data: bytes, error: str) -> None:
    app.state.service.settings.pdf_max_pages = 1
    with TestClient(app) as c:
        before = app.state.service.snapshot("northline")["documents"]
        r = c.post(
            "/api/knowledge/import?name=bad.pdf",
            headers={**headers(app), "Content-Type": "application/pdf"},
            content=data,
        )
        assert r.status_code == 422
        assert r.json()["error"] == error
        assert app.state.service.snapshot("northline")["documents"] == before


def test_concurrent_pdf_limit_rejects_excess_work_and_releases_capacity(
    app: FastAPI, monkeypatch: pytest.MonkeyPatch
) -> None:
    entered, release = threading.Event(), threading.Event()
    calls = []

    def controlled_parser(*args: object) -> str:
        calls.append(True)
        if len(calls) == 1:
            entered.set()
            assert release.wait(5)
        return "Synthetic PDF warranty information."

    monkeypatch.setattr("voicebridge.api.parse_pdf", controlled_parser)
    with TestClient(app) as c, ThreadPoolExecutor(max_workers=1) as pool:

        def send():
            return c.post(
                "/api/knowledge/import?name=controlled.pdf",
                headers={**headers(app), "Content-Type": "application/pdf"},
                content=b"test-pdf-parser-input",
            )

        first = pool.submit(send)
        try:
            assert entered.wait(5)
            excess = send()
            assert excess.status_code == 429
            assert excess.json()["error"] == "pdf_capacity_busy"
            assert len(calls) == 1
        finally:
            release.set()
        assert first.result().status_code == 200
        assert send().status_code == 200
