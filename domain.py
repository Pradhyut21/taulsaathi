"""Conservative, bounded Kannada/English receipt grammar. No model training.

This parser is a prototype hypothesis generator, never an ASR confidence score.
Unknown speech stays visible and blocking checks require human review.
"""
from __future__ import annotations

import hashlib
import re
import uuid
from copy import deepcopy
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

FIELDS = ("material", "gross_kg", "tare_kg", "net_kg", "rate_inr_per_kg")
LABELS = {
    "gross_kg": r"(?:gross(?:\s+weight)?|ಒಟ್ಟು(?:\s+ತೂಕ)?)",
    "tare_kg": r"(?:tare(?:\s+weight)?|bag(?:\s+weight)?|ಚೀಲ(?:ದ)?(?:\s+ತೂಕ)?)",
    "net_kg": r"(?:net(?:\s+weight)?|ನಿವ್ವಳ(?:\s+ತೂಕ)?)",
    "rate_inr_per_kg": r"(?:rate|ದರ)",
}
NUMBERS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
    "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18,
    "nineteen": 19, "twenty": 20, "thirty": 30, "forty": 40,
    "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
    "ಸೊನ್ನೆ": 0, "ಒಂದು": 1, "ಎರಡು": 2, "ಮೂರು": 3, "ನಾಲ್ಕು": 4,
    "ಐದು": 5, "ಆರು": 6, "ಏಳು": 7, "ಎಂಟು": 8, "ಒಂಬತ್ತು": 9,
    "ಹತ್ತು": 10, "ಹನ್ನೊಂದು": 11, "ಹನ್ನೆರಡು": 12, "ಹದಿಮೂರು": 13,
    "ಹದಿನಾಲ್ಕು": 14, "ಹದಿನೈದು": 15, "ಹದಿನಾರು": 16, "ಹದಿನೇಳು": 17,
    "ಹದಿನೆಂಟು": 18, "ಹತ್ತೊಂಬತ್ತು": 19, "ಇಪ್ಪತ್ತು": 20, "ಇಪ್ಪತ್ತೈದು": 25,
    "ಮೂವತ್ತು": 30, "ನಲವತ್ತು": 40, "ನಲ್ವತ್ತು": 40, "ಐವತ್ತು": 50,
    "ಅರವತ್ತು": 60, "ಎಪ್ಪತ್ತು": 70, "ಎಂಬತ್ತು": 80, "ತೊಂಬತ್ತು": 90,
    "ನೂರು": 100,
}
DIGITS = str.maketrans("೦೧೨೩೪೫೬೭೮೯", "0123456789")
KG = r"(?:kg|kgs|kilogram(?:s)?|kilo(?:s)?|ಕೆ\s*ಜಿ|ಕಿಲೋ(?:ಗ್ರಾಂ)?)"
RATE_UNIT = rf"(?:(?:rupees?|rs\.?|ರೂಪಾಯಿ|ರೂ\.?|₹)\s*)?(?:per\s+{KG}|/\s*{KG}|ಪ್ರತಿ\s*{KG}|{KG}\s*ಗೆ)"
MATERIALS = {
    "paper": r"paper|newspapers?|ಕಾಗದ|ಪೇಪರ್",
    "plastic": r"plastic|ಪ್ಲಾಸ್ಟಿಕ್",
    "iron": r"iron|ಕಬ್ಬಿಣ",
    "cardboard": r"cardboard|ರಟ್ಟು",
    "aluminium": r"alumin(?:i)?um|ಅಲ್ಯೂಮಿನಿಯಂ",
    "copper": r"copper|ತಾಮ್ರ",
}


def _d(value: object) -> Decimal:
    if isinstance(value, bool):
        raise ValueError("A number is required.")
    try:
        v = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError("Use a non-negative decimal number.") from None
    if not v.is_finite() or v < 0 or v > Decimal("100000"):
        raise ValueError("Prototype accepts values from 0 to 100000 only.")
    if v.as_tuple().exponent < -3:
        raise ValueError("Use at most three decimal places.")
    return v


def _s(value: Decimal) -> str:
    return format(value.normalize(), "f")


def parse_number(raw: str) -> Decimal | None:
    """Small explicit lexicon; unsupported compounds deliberately return None."""
    raw = raw.strip().lower().translate(DIGITS)
    # An explicit decimal marker separates a bounded whole number from one to
    # three fractional digits. 'point fifteen' is deliberately not inferred as
    # .15; only digit words (zero..nine) and literal digit strings are accepted.
    decimal_parts = re.split(r"\s+(?:point|ಪಾಯಿಂಟ್|ದಶಮಾಂಶ)\s+", raw)
    if len(decimal_parts) > 1:
        if len(decimal_parts) != 2:
            return None
        whole = parse_number(decimal_parts[0])
        if whole is None or whole != whole.to_integral_value():
            return None
        fraction = []
        for token in decimal_parts[1].split():
            if re.fullmatch(r"[0-9]{1,3}", token):
                fraction.extend(token)
            elif token in NUMBERS and 0 <= NUMBERS[token] <= 9:
                fraction.append(str(NUMBERS[token]))
            else:
                return None
        if not 1 <= len(fraction) <= 3:
            return None
        try:
            return _d(f"{_s(whole)}.{''.join(fraction)}")
        except ValueError:
            return None
    # Only an attached English compound such as 'fifty-five' is supported.
    # A leading sign or spaced/repeated dash can mean negative/subtraction;
    # replacing every dash would silently turn '- fifty five' into +55.
    if "-" in raw and not re.fullmatch(r"[a-z]+-[a-z]+", raw):
        return None
    raw = raw.replace("-", " ")
    if re.fullmatch(r"\d+(?:\.\d{1,3})?", raw):
        try:
            return _d(raw)
        except ValueError:
            return None
    if raw in NUMBERS:
        return Decimal(NUMBERS[raw])
    if raw in ("half", "ಅರ್ಧ"):
        return Decimal("0.5")
    if raw in ("one and a half", "ಒಂದೂವರೆ"):
        return Decimal("1.5")
    if raw in ("two and a half", "ಎರಡೂವರೆ"):
        return Decimal("2.5")
    words = raw.split()
    if len(words) == 2 and words[0] in NUMBERS and words[1] in NUMBERS:
        a, b = NUMBERS[words[0]], NUMBERS[words[1]]
        if 20 <= a <= 90 and a % 10 == 0 and 1 <= b <= 9:
            return Decimal(a + b)
    return None


def parse_transcript(transcript: str) -> tuple[dict, list, list]:
    """Require labelled fields and explicit units. Repeated numbers conflict."""
    fields = dict.fromkeys(FIELDS)
    evidence, issues = [], []
    lower = transcript.lower()
    found_materials = []
    for material, pattern in MATERIALS.items():
        for match in re.finditer(rf"(?<!\w)(?:{pattern})(?!\w)", lower):
            found_materials.append(material)
            evidence.append({"field": "material", "raw": transcript[match.start():match.end()],
                             "value": material, "start": match.start(), "end": match.end()})
    if len(set(found_materials)) == 1:
        fields["material"] = found_materials[0]
    elif len(set(found_materials)) > 1:
        issues.append("Multiple materials found. This prototype supports one material per receipt.")

    labels = []
    for field, pattern in LABELS.items():
        for match in re.finditer(rf"(?<!\w){pattern}(?!\w)\s*[:=]?\s*", lower):
            labels.append((match.start(), match.end(), field))
    labels.sort()
    for index, (start, end, field) in enumerate(labels):
        stop = labels[index + 1][0] if index + 1 < len(labels) else len(lower)
        # Do not let a field consume another sentence/turn.
        fragment = re.split(r"[,;\n!?]", lower[end:stop], maxsplit=1)[0].strip()
        unit_pattern = RATE_UNIT if field == "rate_inr_per_kg" else KG
        unit = re.search(rf"(?<!\w){unit_pattern}(?!\w)", fragment)
        number_raw = fragment[:unit.start()].strip() if unit else ""
        # Currency prefix may precede the rate number.
        if field == "rate_inr_per_kg":
            number_raw = re.sub(r"^(?:₹|rs\.?|rupees?|ರೂಪಾಯಿ|ರೂ\.?)\s*", "", number_raw)
        value = parse_number(number_raw) if number_raw else None
        # Anything after the unit except punctuation / conjunctions is suspicious.
        tail = fragment[unit.end():].strip(" .।॥") if unit else fragment
        if tail not in ("", "and", "ಮತ್ತು"):
            issues.append(f"Review extra words after {field}: {tail[:90]}")
        if value is None:
            issues.append(f"Could not safely parse {field}; say a labelled number and explicit unit.")
            continue
        raw_end = end + lower[end:stop].find(fragment) + unit.end()
        evidence.append({"field": field, "raw": transcript[start:raw_end], "value": _s(value),
                         "start": start, "end": raw_end})
        if fields[field] is not None and fields[field] != _s(value):
            fields[field] = None
            issues.append(f"Conflicting {field} values. Choose the intended value explicitly.")
        elif not any(e["field"] == field for e in evidence[:-1]):
            fields[field] = _s(value)
    # Negation/corrections are never silently interpreted as final values.
    if re.search(r"(?<!\w)(?:not|no|sorry|instead|correction|ಅಲ್ಲ|ಬದಲು|ಕ್ಷಮಿಸಿ)(?!\w)", lower):
        issues.append("Spoken correction or negation detected. Review and explicitly resolve the affected field.")
    # Catch unlabelled numbers outside recognized evidence. These may be a second line item.
    masked = list(lower)
    for e in evidence:
        for i in range(e["start"], min(e["end"], len(masked))):
            masked[i] = " "
    remaining = "".join(masked)
    if re.search(r"\d|[೦-೯]", remaining):
        issues.append("Unassigned digits remain in the transcript. Review the transcript before confirming.")
    # Numeric words outside field spans cannot be assumed harmless.
    if any(re.search(rf"(?<!\w){re.escape(w)}(?!\w)", remaining) for w in NUMBERS):
        issues.append("Unassigned number words remain in the transcript. Resolve them explicitly.")
    # A complete record followed by 'cancel', another material, an unsupported
    # fraction or an instruction must not look safe merely because numbers fit.
    leftover = re.sub(r"(?<!\w)(?:and|ಮತ್ತು)(?!\w)", "", remaining)
    if re.search(r"\w", leftover):
        issues.append("Unassigned words remain in the transcript. Check for cancellation, corrections or another item.")
    # Currency, math and cancellation symbols outside recognized evidence can
    # change the transaction. Allow only ordinary prose separators (including
    # Kannada/Indic danda); unsupported symbols require explicit review.
    if re.search(r"[^\w\s,;.!?:'\"()\[\]{}।॥]", leftover):
        issues.append("Unassigned symbols remain in the transcript. Review currency, arithmetic or cancellation marks.")
    return fields, evidence, list(dict.fromkeys(issues))


def recalculate(draft: dict) -> dict:
    f = draft["fields"]
    issues = list(draft.get("parse_issues", []))
    computed = {"net_kg": None, "total_inr": None}
    if not f["material"]:
        issues.append("Select one material.")
    gross, tare, net, rate = (Decimal(f[k]) if f[k] is not None else None
                            for k in ("gross_kg", "tare_kg", "net_kg", "rate_inr_per_kg"))
    if gross is not None and tare is not None:
        if gross <= tare:
            issues.append("Gross weight must exceed tare weight.")
        else:
            derived = gross - tare
            computed["net_kg"] = _s(derived)
            if net is not None and net != derived:
                issues.append("Stated net weight differs from gross minus tare.")
    elif net is not None and gross is None and tare is None:
        computed["net_kg"] = _s(net)
    else:
        issues.append("Provide net kg, or both gross kg and tare kg. No weight is assumed.")
    if computed["net_kg"] is not None and Decimal(computed["net_kg"]) <= 0:
        issues.append("Net weight must be greater than zero.")
    if rate is None or rate <= 0:
        issues.append("Provide a positive INR-per-kg rate.")
    if computed["net_kg"] is not None and rate is not None:
        total = (Decimal(computed["net_kg"]) * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        computed["total_inr"] = format(total, ".2f")
    draft["computed"], draft["issues"] = computed, list(dict.fromkeys(issues))
    draft["can_confirm"] = not issues and draft["status"] != "confirmed"
    draft["readback_text"] = readback(draft)
    return draft


def readback(draft: dict) -> str:
    c, f = draft["computed"], draft["fields"]
    if c["net_kg"] is None or c["total_inr"] is None or not f["material"]:
        return "Resolve the missing or conflicting fields before requesting a readback."
    net, rate, total = c["net_kg"], f["rate_inr_per_kg"], c["total_inr"]
    def spoken(number):
        words = (["ಸೊನ್ನೆ", "ಒಂದು", "ಎರಡು", "ಮೂರು", "ನಾಲ್ಕು", "ಐದು", "ಆರು", "ಏಳು", "ಎಂಟು", "ಒಂಬತ್ತು"]
                 if draft["language"] == "kn-IN" else
                 ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"])
        point = "ದಶಮಾಂಶ" if draft["language"] == "kn-IN" else "point"
        return " ".join(point if char == "." else words[int(char)] for char in number)
    if draft["language"] == "kn-IN":
        material = {"paper":"ಕಾಗದ", "plastic":"ಪ್ಲಾಸ್ಟಿಕ್", "iron":"ಕಬ್ಬಿಣ", "cardboard":"ರಟ್ಟು",
                    "aluminium":"ಅಲ್ಯೂಮಿನಿಯಂ", "copper":"ತಾಮ್ರ"}.get(f["material"], f["material"])
        # Native-speaker and live-TTS checks are required before contest claims.
        inputs = (f"ಒಟ್ಟು ತೂಕ {spoken(f['gross_kg'])} ಕಿಲೋಗ್ರಾಂ. ಚೀಲದ ತೂಕ {spoken(f['tare_kg'])} ಕಿಲೋಗ್ರಾಂ. "
                  if f["gross_kg"] is not None and f["tare_kg"] is not None else "")
        return f"{material}. {inputs}ನಿವ್ವಳ ತೂಕ {spoken(net)} ಕಿಲೋಗ್ರಾಂ. ಪ್ರತಿ ಕಿಲೋಗ್ರಾಂಗೆ {spoken(rate)} ರೂಪಾಯಿ. ಒಟ್ಟು {spoken(total)} ರೂಪಾಯಿ. ದಯವಿಟ್ಟು ತೂಕ ಮತ್ತು ದರ ಪರಿಶೀಲಿಸಿ."
    inputs = (f"Gross weight {spoken(f['gross_kg'])} kilograms. Tare weight {spoken(f['tare_kg'])} kilograms. "
              if f["gross_kg"] is not None and f["tare_kg"] is not None else "")
    return (f"{f['material']}. {inputs}Net weight {spoken(net)} kilograms. Rate {spoken(rate)} rupees per kilogram. "
            f"Total {spoken(total)} rupees. Please check the weight and rate before confirming.")


def create_draft(transcript: str, language: str = "kn-IN", source: str = "typed") -> dict:
    if not isinstance(transcript, str) or not transcript.strip() or len(transcript) > 4000:
        raise ValueError("Enter a transcript of 1 to 4000 characters.")
    if language not in ("kn-IN", "en-IN"):
        raise ValueError("Prototype supports Kannada and English only.")
    if source not in ("typed", "synthetic", "gnani"):
        raise ValueError("Invalid transcript source.")
    fields, evidence, parse_issues = parse_transcript(transcript)
    return recalculate({"id": uuid.uuid4().hex, "revision": 1, "status": "draft",
                        "language": language, "transcript": transcript, "source": source,
                        "fields": fields, "evidence": evidence, "parse_issues": parse_issues,
                        "history": [{"action":"created", "detail":f"Source: {source}", "revision":1}]})


def revise(draft: dict, revision: int, field: str, value: str, reason: str) -> dict:
    if revision != draft["revision"]:
        raise ValueError("This revision is stale. Reload the latest draft.")
    if field not in FIELDS:
        raise ValueError("Unknown field.")
    if not isinstance(reason, str) or not 3 <= len(reason.strip()) <= 300:
        raise ValueError("Explain the correction in 3 to 300 characters.")
    if field == "material":
        if value not in MATERIALS:
            raise ValueError("Select one of the supported materials.")
    elif value in ("", None):
        value = None
    else:
        value = _s(_d(value))
    updated = deepcopy(draft)
    old = updated["fields"][field]
    updated["fields"][field] = value
    updated["revision"] += 1
    updated["status"] = "draft"
    updated.pop("digest", None)
    # A review must explicitly acknowledge every parse warning, not just edit any field.
    # Warnings persist until resolve_review() is called after field corrections.
    updated["history"].append({"action":"corrected", "revision":updated["revision"],
                               "detail":f"{field}: {old} -> {value}. {reason.strip()}"})
    return recalculate(updated)


def resolve_review(draft: dict, revision: int, reason: str) -> dict:
    if revision != draft["revision"]:
        raise ValueError("This revision is stale. Reload the latest draft.")
    if not isinstance(reason, str) or not 8 <= len(reason.strip()) <= 300:
        raise ValueError("Describe how you checked the transcript in 8 to 300 characters.")
    updated = deepcopy(draft)
    updated["revision"] += 1
    updated["status"] = "draft"
    updated.pop("digest", None)
    updated["parse_issues"] = []
    updated["history"].append({"action":"reviewed", "revision":updated["revision"],
                               "detail":f"Operator resolved transcript warnings: {reason.strip()}"})
    return recalculate(updated)


def confirm(draft: dict, revision: int, reviewed: bool) -> dict:
    if revision != draft["revision"]:
        raise ValueError("Cannot confirm a stale revision.")
    if reviewed is not True:
        raise ValueError("Explicitly review the weight, rate and total first.")
    if draft["status"] == "confirmed":
        return deepcopy(draft)
    if not draft["can_confirm"]:
        raise ValueError("Resolve all blocking issues before confirmation.")
    updated = deepcopy(draft)
    snapshot = {k: updated[k] for k in ("id", "revision", "language", "fields", "computed")}
    updated["digest"] = hashlib.sha256(__import__("json").dumps(snapshot, sort_keys=True).encode()).hexdigest()
    updated["status"] = "confirmed"
    updated["can_confirm"] = False
    updated["history"].append({"action":"confirmed", "detail":"Operator reviewed this exact revision; no payment executed.",
                               "revision":revision})
    return updated
