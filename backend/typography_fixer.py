import re

_WEEKDAY = "(?:Mo|Di|Mi|Do|Fr|Sa|So)"
_ROMAN_NUMERAL = "(?:I|II|III|IV|V|VI|VII|VIII|IX|X)"
_TIME = r"(?:\d{1,2}[:.]\d{2})"
_NUM = r"(?:\d+(?:,\d+)?)"

_REGEXES = {
    "whitespace": [
        # deduplicate whitespace
        (r" {1,3}", " "),

        # insert whitespace after abbreviation dot
        # (?<!\S)
        (r"\b(\d+\.)\b(?!\d)", r"\1 "),  # 1.Stunde
        # (?<!\d)
        (rf"(\D)\b\.({_ROMAN_NUMERAL}|\d+)\b", r"\1. \2"),  # Sek.I; Jg.12

        # before parens
        (r"\( ", "("),
        (r" \)", ")"),

        # before "Uhr"
        (r"(\d)(Uhr)", r"\1 \2"),
    ],
    "slashes": [
        (r"\b/ {1,3}\b", "/"),
        (r"\b /\b", "/"),
        (r"\b {1,3}/ {1,3}\b", " / "),

        (r"\b(\d+\.?)/ {1,3}\b(\d+\.?)\b", r"\1/\2"),
        (r"\b(\d+\.?) /\b(\d+\.?)\b", r"\1/\2"),

        # (r"(?<=\w)/ ", "/")  # remove spaces after slashes like in G/ R/ W
    ],
    "commas": [
        # missing after comma
        (r"(?<!\d)\b ?, ?\b(?!\d)", ", "),
    ],
    "punctuation": [
        (r"\b ([.?!])", r"\1"),
    ],
    "dashes": [
        # Bis-Strich
        (rf"({_WEEKDAY}) ?- ?({_WEEKDAY})", r"\1–\2"),
        (rf"({_TIME}|\d{{1,2}}) ?- ?({_TIME})", r"\1–\2"),
        (rf"(?<![\./:])(\d+) ?- ?(\d+)(?!\.|\s*[+-=*/])", r"\1–\2"),
        (rf"(\d+\.) ?- ?(\d+\.)", r"\1–\2"),

        # Gedankenstrich
        (r"(\)|\b) - (-?)\b", r"\1 – \2"),
    ],
    "colons": [
        # missing whitespace after colon
        (r"(?<!:)\b( +– +:)\b", r"\1 "),

        # whitespace erroneously before colon
        (r"(?<!\d)\b ?: ?\b(?!\d)", ": "),
        (r"\b : \b", ": "),
    ],
    "apostrophes": [
        (r"\b[´`']\b", "’")
    ],
    "units": [
        (rf"\b({_NUM})€", r"\1 €"),
    ],
    "operators": [
        # unbalanced whitespace around +
        (r"\b \+\b", " + "),
        (r"\b\+ \b", " + "),
    ],
    "unary-minus": [
        (r"(?:^|\s)-(\d+)\b", r" −\1"),
    ],
    "operator-minus": [
        (r"\b(\d+) ?- ?(\d+)\b", r"\1−\2"),
    ]
}

REGEXES = {key: [(re.compile(pattern), replace) for pattern, replace in ops] for key, ops in _REGEXES.items()}

TESTS = [
    ("Klasse 6/ 1 geht", "Klasse 6/1 geht"),
    ("Hallo ,  Welt", "Hallo, Welt"),
    ("Klasse 10 (8:00 - 9:50 Uhr)", "Klasse 10 (8:00–9:50 Uhr)"),
    ("1.-2. Block", "1.–2. Block"),
    ("1.-2.Block", "1.–2. Block"),
    ("- alle Schülerhelfer", "- alle Schülerhelfer"),
    ("die Sek.II 9:10 Uhr", "die Sek. II 9:10 Uhr"),
    ("Jahrgänge 8-10 im", "Jahrgänge 8–10 im"),
    ("Nachschreibetermin (2113) - entfällt", "Nachschreibetermin (2113) – entfällt"),
    ("Nachschreibtermin Sek I +Jg.12", "Nachschreibtermin Sek I + Jg. 12"),
    ("JG 9 - 1. -4. Stunde", "JG 9 – 1.–4. Stunde"),
    ("JG 11 - BeLL", "JG 11 – BeLL"),
    ("stehen im V-Plan)", "stehen im V-Plan)"),
    ("gesperrten Türen/  Räumen", "gesperrten Türen/Räumen"),
    ("5/ 4 - -2112 (WNG)", "5/4 – −2112 (WNG)"),
    ("6/ 1 - 1114 (WOL)", "6/1 – 1114 (WOL)"),
    ("Aufsicht RDL ( 45 minütige", "Aufsicht RDL (45 minütige"),
    ("(KPL,THD, PAU ,WEY, KAB, BRN, WBA )", "(KPL, THD, PAU, WEY, KAB, BRN, WBA)"),
    ("zum 30.10. aus.", "zum 30.10. aus."),
    ("14 - 15.30 Uhr", "14–15.30 Uhr"),
    ("13.45Uhr", "13.45 Uhr"),
    ("pünktlich 11.24 Uhr !", "pünktlich 11.24 Uhr!"),
    ("den 09.11.2022, aufgrund", "den 09.11.2022, aufgrund")
]


def run_tests():
    failed = 0
    for inp, out in TESTS:
        fixed = fix_typography(inp)
        if fixed == out:
            print(f"[PASSED] {inp} -> {fixed}")
        else:
            print(f"[FAILED] {inp} -> {out}")
            print(f"         {inp} -> {fixed}")
            failed += 1

    print(f"{len(TESTS) - failed}/{len(TESTS)} tests passed.")


def fix_typography(string: str):
    for ops in REGEXES.values():
        for pattern, replace in ops:
            string = re.sub(pattern, replace, string.strip())

    return string.strip()


def main():
    run_tests()

    import tkinter as tk

    root = tk.Tk()
    root.title("Text Cleaner")

    paned = tk.PanedWindow(root, orient=tk.HORIZONTAL)
    paned.pack(fill="both", expand=True)

    textedit = tk.Text(paned, wrap="word", font="Helvetica")
    paned.add(textedit, stretch="always")

    out_text = tk.Text(paned, wrap="word", font="Helvetica")
    paned.add(out_text, stretch="always")

    def clean():
        out_text.delete("1.0", "end")
        out_text.insert("1.0", fix_typography(textedit.get("1.0", "end")))

    # run clean when text is modified
    textedit.bind("<KeyRelease>", lambda _: clean())

    root.mainloop()


if __name__ == "__main__":
    main()
