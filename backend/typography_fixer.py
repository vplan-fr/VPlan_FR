import re

_WEEKDAY = "(?:Mo|Di|Mi|Do|Fr|Sa|So)"
_ROMAN_NUMERAL = "(?:I|II|III|IV|V|VI|VII|VIII|IX|X)"
_TIME = r"(?:\d{1,2}:\d{2})"
_NUM = r"(?:\d+(?:,\d+)?)"

_REGEXES = {
    "whitespace": [
        # deduplicate whitespace
        (r"\b {1,3}\b", " "),

        # insert whitespace after abbreviation dot
        # (?<!\S)
        (r"\b(\d+\.)\b(?!\d)", r"\1 "),  # 1.Stunde
        # (?<!\d)
        (rf"(\D)\b\.({_ROMAN_NUMERAL}|\d+)\b", r"\1. \2"),  # Sek.I; Jg.12

        # before parens
        (r"\( ", "("),
        (r" \)", ")"),
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
    "dashes": [
        # Bis-Strich
        (rf"({_WEEKDAY}) ?- ?({_WEEKDAY})", r"\1–\2"),
        (rf"({_TIME}) ?- ?({_TIME})", r"\1–\2"),
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


def fix_typography(string: str):
    for ops in REGEXES.values():
        for pattern, replace in ops:
            string = re.sub(pattern, replace, string.strip())

    return string.strip()


def main():
    import tkinter as tk

    root = tk.Tk()
    root.title("Text Cleaner")

    textedit = tk.Text(root, wrap="word", font="Helvetica")
    textedit.pack(side="left", fill="both", expand=True)

    out_text = tk.Text(root, wrap="word", font="Helvetica")
    out_text.pack(side="right", fill="both", expand=True)

    def clean():
        out_text.delete("1.0", "end")
        out_text.insert("1.0", fix_typography(textedit.get("1.0", "end")))

    # run clean when text is modified
    textedit.bind("<KeyRelease>", lambda _: clean())

    root.mainloop()


if __name__ == "__main__":
    main()