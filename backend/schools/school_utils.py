def is_kuerzel_in_name(name, kuerzel):
    name = name.lower()
    abbreviation = kuerzel.lower()
    if abbreviation[0] != name[0]:
        return False
    name_index = 0
    abbreviation_index = 0
    while abbreviation_index < len(abbreviation):
        char = abbreviation[abbreviation_index]
        char_index = name.find(char, name_index)
        if char_index == -1:
            return False
        name_index = char_index + 1
        abbreviation_index += 1
    return True


def names_kuerzel(kuerzels, names):
    names_match = {}
    for name in names:
        names_match[name] = []
        for kuerzel in kuerzels:
            if is_kuerzel_in_name(name.split(" ")[-1], kuerzel):
                names_match[name].append(kuerzel)
    # problem: the kuerzel seem very indefinitive...
    """# error detection should be implemented here (e.g. 2 names that both only have 1 valid kuerzel)
    definite_kuerzel = []
    for name, values in names_match.items():
        if len(values) == 0:
            names_match[name] = None
        if len(values) == 1:
            if values[0] not in definite_kuerzel:
                definite_kuerzel.append(values[0])
            else:
                print(f"conflict for kuerzel {values[0]}")
            names_match[name] = values[0]
    # for name, values in names_match.items():
    #     if type(values) == list:
    #         names_match[name] = [value for value in values if value not in definite_kuerzel]
    """
    return names_match
