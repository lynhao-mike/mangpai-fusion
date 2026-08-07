import pytest

from engine.predicates.career import is_rooted


@pytest.mark.parametrize(
    ("gan", "zhi"),
    [
        ("甲", "寅"),  # 主气
        ("癸", "丑"),  # 中气
        ("辛", "丑"),  # 余气
    ],
)
def test_is_rooted_requires_exact_hidden_stem_membership(gan: str, zhi: str) -> None:
    assert is_rooted(gan, zhi) is True


@pytest.mark.parametrize(
    ("gan", "zhi"),
    [
        ("乙", "寅"),  # 同属木，但寅不藏乙：不得放宽成五行同类
        ("甲", "卯"),  # 同属木，但卯只藏乙
        ("丙", "未"),  # 未藏丁而不藏丙
    ],
)
def test_is_rooted_rejects_same_element_without_exact_stem(gan: str, zhi: str) -> None:
    assert is_rooted(gan, zhi) is False


@pytest.mark.parametrize(
    ("gan", "zhi", "match"),
    [
        ("X", "寅", "invalid gan"),
        ("甲", "X", "invalid zhi"),
    ],
)
def test_is_rooted_rejects_invalid_symbols(gan: str, zhi: str, match: str) -> None:
    with pytest.raises(ValueError, match=match):
        is_rooted(gan, zhi)


def test_is_rooted_is_deterministic_and_returns_bool() -> None:
    outputs = [is_rooted("壬", "亥") for _ in range(3)]

    assert outputs == [True, True, True]
    assert all(type(output) is bool for output in outputs)
