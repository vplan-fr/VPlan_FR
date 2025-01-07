import re

_WEEKDAY = "(?:Mo|Di|Mi|Do|Fr|Sa|So)"
_ROMAN_NUMERAL = "(?:I|II|III|IV|V|VI|VII|VIII|IX|X)"
_TIME = r"(?:\d{1,2}:\d{2})"

REGEXES = {
    "whitespace": [
        # deduplicate whitespace
        (r"\b {1,3}\b", " "),

        # insert whitespace after abbreviation dot
        (r"(?<!\S)\b(\d+\.)\b(?!\d)", r"\1 "),  # 1.Stunde
        # (?<!\d)
        (rf"(\D)\b\.({_ROMAN_NUMERAL}|\d+)\b", r"\1. \2"),  # Sek.I; Jg.12

        # before parens
        (r"\( ", "("),
        (r" \)", ")"),
    ],
    "slashes": [
        (r"\b/ {1,3}\b", "/"),
        (r"(?<=\w)/ ", "/")  # remove spaces after slashes like in G/ R/ W
    ],
    "commas": [
        # missing after comma
        (r"(?<!\d)\b ?, ?\b(?!\d)", ", "),
    ],
    "dashes": [
        # Bis-Strich
        (rf"({_WEEKDAY}) ?- ?({_WEEKDAY})", r"\1–\2"),
        (rf"({_TIME}) ?- ?({_TIME})", r"\1–\2"),
        (rf"(?<!\.)(\d+) ?- ?(\d+)(?!\.)", r"\1–\2"),
        (rf"(\d+\.) ?- ?(\d+\.)", r"\1–\2"),

        # Gedankenstrich
        (r"\b - \b", " – "),
    ],
    "colons": [
        # missing whitespace after colon
        (r"(\w+–\w+:)\b", r"\1 "),

        # whitespace erroneously before colon
        (r"\b :\b", ": "),
    ],
    "apostrophes": [
        (r"\b[´`']\b", "’")
    ],
    "units": [
        (r"\b(\d+(?:,\d+)?)€", r"\1 €"),
    ]
}


def cleanup(string: str):
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
        out_text.insert("1.0", cleanup(textedit.get("1.0", "end")))

    # run clean when text is modified
    textedit.bind("<KeyRelease>", lambda _: clean())

    root.mainloop()


if __name__ == "__main__":
    main()