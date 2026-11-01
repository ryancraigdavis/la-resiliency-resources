import pytest
from pydantic import ValidationError

from la_resiliency.models import Phone, Resource


@pytest.fixture
def minimal():
    return {
        "id": "sample",
        "categories": ["food"],
        "name": "Sample",
        "description": "Free food.",
        "last_verified": "2026-06-30",
    }


@pytest.mark.parametrize(
    "number,tel",
    [
        pytest.param("(888) 624-4752", "+18886244752", id="parens"),
        pytest.param("888-624-4752", "+18886244752", id="dashes"),
        pytest.param("1-800-510-2020", "+18005102020", id="leading-one"),
        pytest.param("+1 714.477.2958", "+17144772958", id="plus-dots"),
        pytest.param("211", "211", id="n11-short-code"),
    ],
)
def test_phone_tel(number, tel):
    assert Phone(number=number).tel == tel


@pytest.mark.parametrize(
    "number",
    [
        pytest.param("624-4752", id="no-area-code"),
        pytest.param("call 211", id="words"),
        pytest.param("(888) 624-47521", id="too-long"),
    ],
)
def test_phone_rejects_bad_numbers(number):
    with pytest.raises(ValidationError):
        Phone(number=number)


@pytest.mark.parametrize(
    "changes",
    [
        pytest.param({"id": "Has Spaces"}, id="bad-slug"),
        pytest.param({"url": "www.example.org"}, id="url-without-scheme"),
        pytest.param({"categories": []}, id="no-category"),
        pytest.param({"description": "   "}, id="blank-description"),
        pytest.param({"audience": "kids"}, id="unknown-audience"),
        pytest.param({"languages": ["spanish"]}, id="language-name-not-code"),
        pytest.param({"extra": "field"}, id="unknown-field"),
    ],
)
def test_resource_rejects_invalid(minimal, changes):
    with pytest.raises(ValidationError):
        Resource.model_validate(minimal | changes)


def test_resource_defaults(minimal):
    resource = Resource.model_validate(minimal)
    assert (resource.audience, resource.active, resource.phones) == ("everyone", True, [])
