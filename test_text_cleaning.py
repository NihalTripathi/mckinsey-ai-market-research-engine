
from types import SimpleNamespace

from agents.report import clean_text


def evidence(topic="demand", claim="General research evidence"):
    return SimpleNamespace(
        topic=topic,
        claim=claim
    )


def check(name, condition):
    status = "PASS" if condition else "FAIL"
    print(f"{status}  {name}")

    if not condition:
        raise AssertionError(name)


def run_tests():

    aliases = {
        "E1": evidence("demand"),
        "E2": evidence("policy"),
        "E3": evidence("market size"),
    }

    # 1. Different research industries.
    samples = [
        "Artificial intelligence is changing business operations [E1].",
        "Healthcare technology is improving patient services [E1].",
        "Banking institutions are adopting digital services [E1].",
        "Agricultural technology supports farm productivity [E1].",
        "Renewable energy is an important research area [E1].",
    ]

    for i, sample in enumerate(samples, start=1):
        result = clean_text(sample, aliases)
        check(
            f"Industry example {i} retains valid citation",
            "[E1]" in result
        )

    # 2. Preserve company names and technical terminology.
    text = (
        "OpenAI and TataPower are examples of company names [E1]."
    )
    result = clean_text(text, aliases)

    check(
        "Company names are not automatically split",
        "TataPower" in result and "OpenAI" in result
    )

    # 3. Preserve acronyms and technical terms.
    text = "AI, ML, API, GDP and CAGR are retained [E1]."
    result = clean_text(text, aliases)

    check(
        "Technical abbreviations are preserved",
        all(term in result for term in ["AI", "ML", "API", "GDP", "CAGR"])
    )

    # 4. Preserve numerical formatting.
    text = "The reported value was 5,500 units [E1]."
    result = clean_text(text, aliases)

    check(
        "Unsupported-number filtering remains active",
        result == ""
    )

    # 5. Remove invalid citations.
    text = "This is a general research statement [E99]."
    result = clean_text(text, aliases)

    check(
        "Invalid citation is removed",
        "[E99]" not in result
    )

    # 6. Preserve valid citations and add spacing.
    text = "The market is developing[E1]."
    result = clean_text(text, aliases)

    check(
        "Space before citation is added",
        "developing [E1]" in result
    )

    # 7. Policy claims receive a verification reminder.
    text = "The policy supports the industry [E2]."
    result = clean_text(text, aliases)

    check(
        "Policy verification reminder is added",
        "verify the current status" in result.lower()
    )

    # 8. Trend blocking.
    text = "The market is growing rapidly [E3]."
    result = clean_text(text, aliases, block_trend=True)

    check(
        "Market-size trend blocking works",
        result == ""
    )



    # 8. Repair common missing-space errors without splitting names.
    from agents.report import _repair_report_spacing

    repaired = _repair_report_spacing(
        "Startup activity,investment figures in2025and 2026."
    )
    check(
        "Joined year and comma spacing are repaired",
        "activity, investment" in repaired
        and "in 2025 and 2026" in repaired
    )

    names = _repair_report_spacing(
        "TataPower,OpenAI and NVIDIA provide examples."
    )
    check(
        "Company and product names are preserved",
        "TataPower" in names and "OpenAI" in names and "NVIDIA" in names
    )

    print("\nAll text-cleaning tests passed.")


if __name__ == "__main__":
    run_tests()
