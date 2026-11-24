"""Large public catalogs must not spend the request budget compiling absent names."""
import re
from unittest.mock import patch

from onmaru_ai.query.dictionary import CatalogEntry, match_mentions


def test_absent_catalog_names_do_not_compile_patterns() -> None:
    catalog = tuple(
        CatalogEntry(code=f'p-{i}', kind='PLACE', display_label=f'다른관광지{i}')
        for i in range(23573)
    ) + (
        CatalogEntry(code='palace-a', kind='PLACE', display_label='경복궁'),
        CatalogEntry(code='palace-b', kind='PLACE', display_label='경복궁'),
        CatalogEntry(code='literal', kind='PLACE', display_label='궁(별관)'),
    )
    with patch('onmaru_ai.query.dictionary.re.compile', wraps=re.compile) as compile_pattern:
        mentions = match_mentions('경복궁의 역사와 궁(별관)을 설명해 줘', catalog)
    assert len(compile_pattern.call_args_list) <= 4
    assert [(m.kind, m.codes) for m in mentions] == [
        ('PLACE', ('palace-a', 'palace-b')),
        ('CONCEPT', ('HISTORY',)),
        ('PLACE', ('literal',)),
    ]
