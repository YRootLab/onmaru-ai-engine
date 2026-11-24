"""Smoke-test the final container interpreter, native wheels, CA store and E5."""
from __future__ import annotations

import importlib
import json
import ssl
import sys

from onmaru_ai.embedding import E5_SMALL_ONNX_INT8_384, EmbeddingService, load_e5_backend


def main() -> None:
    if sys.version_info[:2] != (3, 12) or sys.prefix != '/app/.venv':
        raise RuntimeError('unexpected container interpreter or virtual environment')
    for module in ('numpy', 'onnxruntime', 'sentencepiece', 'tokenizers', 'psycopg',
                   'uvloop', 'httptools', 'watchfiles'):
        importlib.import_module(module)
    if ssl.create_default_context().cert_store_stats()['x509_ca'] == 0:
        raise RuntimeError('container CA store is empty')
    service = EmbeddingService(load_e5_backend('/opt/onmaru/e5'), profile=E5_SMALL_ONNX_INT8_384)
    vector = service.embed_query('경복궁의 창건 역사')
    if len(vector) != 384 or abs(sum(value * value for value in vector) - 1) >= 0.01:
        raise RuntimeError('invalid E5 query vector')
    print(json.dumps({'python': sys.version.split()[0], 'dimensions': len(vector)}))


if __name__ == '__main__':
    main()
