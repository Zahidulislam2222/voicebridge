"""PDF parsing runs in a disposable process with memory, CPU and wall-time limits."""

import io
import json
import logging
import math
import multiprocessing
from multiprocessing.connection import Connection

from pypdf import PdfReader

from .contracts import DomainError
from .settings import Settings


def parse_child(
    sender: Connection, body: bytes, pages: int, memory: int, timeout: float, output_bytes: int
) -> None:
    try:
        import resource

        logging.getLogger("pypdf").disabled = True
        resource.setrlimit(resource.RLIMIT_AS, (memory, memory))
        cpu = math.ceil(timeout)
        resource.setrlimit(resource.RLIMIT_CPU, (cpu, cpu))
        reader = PdfReader(io.BytesIO(body), strict=True)
        if reader.is_encrypted:
            raise DomainError("encrypted_pdf_unsupported", 422)
        if len(reader.pages) > pages:
            raise DomainError("pdf_page_limit", 422)
        parts = []
        size = 0
        for page in reader.pages:
            value = page.extract_text()
            size += len(value.encode("utf-8")) + 1
            if size > output_bytes:
                raise DomainError("document_too_large", 422)
            parts.append(value)
        text = "\n".join(parts)
        if not text.strip():
            raise DomainError("scanned_pdf_unsupported", 422)
        response = {"text": text}
    except DomainError as exc:
        response = {"error": exc.code}
    except (Exception, MemoryError):
        # Parser exceptions never disclose document bytes, paths or internals.
        response = {"error": "document_parse_failed"}
    try:
        sender.send_bytes(json.dumps(response).encode("utf-8"))
    finally:
        sender.close()


def parse_pdf(body: bytes, settings: Settings) -> str:
    context = multiprocessing.get_context("spawn")
    receiver, sender = context.Pipe(duplex=False)
    process = context.Process(
        target=parse_child,
        args=(
            sender,
            body,
            settings.pdf_max_pages,
            settings.pdf_memory_bytes,
            settings.pdf_timeout_seconds,
            settings.max_document_bytes,
        ),
        daemon=True,
    )
    try:
        process.start()
        sender.close()
        if not receiver.poll(settings.pdf_timeout_seconds):
            raise DomainError("pdf_resource_limit", 422)
        try:
            response = json.loads(receiver.recv_bytes(settings.max_document_bytes * 6))
        except (EOFError, OSError, ValueError) as exc:
            raise DomainError("pdf_resource_limit", 422) from exc
        if "error" in response:
            raise DomainError(response["error"], 422)
        return str(response["text"])
    finally:
        receiver.close()
        sender.close()
        if process.pid is not None:
            if process.is_alive():
                process.terminate()
            process.join()
            process.close()
