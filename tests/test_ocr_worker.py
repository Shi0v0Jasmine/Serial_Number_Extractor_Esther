from __future__ import annotations

from serial_extractor.ocr_worker import parse_paddle_result


class PaddleResultObject:
    @property
    def json(self):
        return {
            "res": {
                "rec_texts": ["S/N", "FA7O2612O1473"],
                "rec_scores": [0.99, 0.73],
                "rec_polys": [
                    [[10, 10], [40, 10], [40, 20], [10, 20]],
                    [[50, 10], [160, 10], [160, 20], [50, 20]],
                ],
            }
        }


def test_parse_paddle_result_preserves_raw_ambiguous_characters() -> None:
    spans = parse_paddle_result(PaddleResultObject(), page_number=3)

    assert spans == [
        {
            "text": "S/N",
            "page": 3,
            "bbox": [10.0, 10.0, 40.0, 20.0],
            "confidence": 0.99,
        },
        {
            "text": "FA7O2612O1473",
            "page": 3,
            "bbox": [50.0, 10.0, 160.0, 20.0],
            "confidence": 0.73,
        },
    ]


def test_parse_paddle_result_supports_flat_box_payload() -> None:
    payload = {
        "rec_texts": ["FA70000000001"],
        "rec_scores": [0.98],
        "rec_boxes": [[1, 2, 101, 22]],
    }

    assert parse_paddle_result(payload, 1)[0]["bbox"] == [1.0, 2.0, 101.0, 22.0]


class ArrayLike:
    def __init__(self, value):
        self.value = value

    def tolist(self):
        return self.value


def test_parse_paddle_result_supports_numpy_like_arrays() -> None:
    payload = {
        "rec_texts": ArrayLike(["FA70000000001"]),
        "rec_scores": ArrayLike([0.97]),
        "rec_polys": ArrayLike([[[1, 2], [101, 2], [101, 22], [1, 22]]]),
    }

    assert parse_paddle_result(payload, 2) == [
        {
            "text": "FA70000000001",
            "page": 2,
            "bbox": [1.0, 2.0, 101.0, 22.0],
            "confidence": 0.97,
        }
    ]
