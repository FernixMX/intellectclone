"""
Fixture de respuesta OpenAlex para tests de OpenAlexHarvester.
"""

from __future__ import annotations

from typing import Any

WORK_COMPLETO: dict[str, Any] = {
    "id": "https://openalex.org/W2741809807",
    "doi": "https://doi.org/10.1016/j.neunet.2020.01.001",
    "title": "Redes Neuronales Artificiales: Una Revisión",
    "publication_year": 2020,
    "publication_date": "2020-03-15",
    "language": "es",
    "type": "journal-article",
    "cited_by_count": 42,
    "abstract_inverted_index": {
        "Las": [0],
        "redes": [1],
        "neuronales": [2],
        "artificiales": [3],
        "son": [4],
        "modelos": [5],
        "computacionales": [6],
        "inspirados": [7],
        "en": [8],
        "el": [9],
        "cerebro": [10],
        "humano": [11],
    },
    "primary_location": {
        "source": {
            "display_name": "Neural Networks",
            "issn_l": "0893-6080",
            "host_organization": "Elsevier",
        },
        "pdf_url": "https://example.com/paper.pdf",
        "landing_page_url": "https://doi.org/10.1016/j.neunet.2020.01.001",
    },
    "biblio": {
        "volume": "125",
        "issue": "3",
        "first_page": "100",
        "last_page": "115",
    },
    "open_access": {
        "is_oa": True,
        "oa_status": "gold",
    },
    "counts_by_year": [
        {"year": 2020, "cited_by_count": 5},
        {"year": 2021, "cited_by_count": 15},
        {"year": 2022, "cited_by_count": 22},
    ],
    "concepts": [
        {"display_name": "Artificial neural network", "score": 0.95},
        {"display_name": "Deep learning", "score": 0.82},
        {"display_name": "Machine learning", "score": 0.78},
    ],
    "authorships": [
        {
            "author_position": "first",
            "is_corresponding": True,
            "author": {
                "id": "https://openalex.org/A2208157607",
                "display_name": "María Elena Cárdenas Ruiz",
                "orcid": "https://orcid.org/0000-0002-1234-5678",
            },
            "institutions": [
                {
                    "id": "https://openalex.org/I4210158051",
                    "ror": "https://ror.org/00qm7vk32",
                    "display_name": "Universidad Autónoma de Tamaulipas",
                }
            ],
            "raw_affiliation_strings": ["Universidad Autónoma de Tamaulipas, México"],
        },
        {
            "author_position": "middle",
            "is_corresponding": False,
            "author": {
                "id": "https://openalex.org/A999888777",
                "display_name": "John Doe",
                "orcid": None,
            },
            "institutions": [
                {
                    "id": "https://openalex.org/I1000000",
                    "ror": "https://ror.org/otroror",
                    "display_name": "MIT",
                }
            ],
            "raw_affiliation_strings": ["MIT, USA"],
        },
    ],
}

WORK_MINIMO: dict[str, Any] = {
    "id": "https://openalex.org/W9999999999",
    "doi": None,
    "title": "Título mínimo sin abstract ni venue",
    "publication_year": 2021,
    "publication_date": None,
    "language": None,
    "type": "unknown-type",
    "cited_by_count": 0,
    "abstract_inverted_index": None,
    "primary_location": None,
    "biblio": {},
    "open_access": None,
    "counts_by_year": [],
    "concepts": [],
    "authorships": [],
}

PAGE_1_RESPONSE: dict[str, Any] = {
    "meta": {
        "count": 3,
        "per_page": 2,
        "cursor": "*",
        "next_cursor": "cursor_pagina_2",
    },
    "results": [WORK_COMPLETO, WORK_MINIMO],
}

PAGE_2_RESPONSE: dict[str, Any] = {
    "meta": {
        "count": 3,
        "per_page": 2,
        "cursor": "cursor_pagina_2",
        "next_cursor": None,
    },
    "results": [
        {
            **WORK_COMPLETO,
            "id": "https://openalex.org/W1111111111",
            "doi": "https://doi.org/10.9999/otro.paper",
            "title": "Tercer paper de la paginación",
        }
    ],
}
