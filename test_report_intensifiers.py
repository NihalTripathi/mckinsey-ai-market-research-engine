"""The report writer must not add intensifier words the cited evidence does not use."""

from types import SimpleNamespace

from agents.report import clean_text


def _alias(claim):
    return {"E1": SimpleNamespace(claim=claim, topic="talent")}


def test_added_intensifier_is_removed():
    out = clean_text(
        "There is a significant talent shortage [E1].",
        _alias("India has a talent shortage."),
    )
    assert "significant" not in out.lower()
    assert "talent shortage" in out
    assert "[E1]" in out


def test_intensifier_used_by_evidence_is_kept():
    out = clean_text(
        "There is a significant talent shortage [E1].",
        _alias("A significant talent shortage exists."),
    )
    assert "significant" in out


def test_first_word_stays_capitalised():
    out = clean_text(
        "Significant infrastructure investment is under way [E1].",
        _alias("Infrastructure investment is under way."),
    )
    assert out.startswith("Infrastructure investment")


if __name__ == "__main__":
    test_added_intensifier_is_removed()
    test_intensifier_used_by_evidence_is_kept()
    test_first_word_stays_capitalised()
    print("Intensifier rule tests passed.")