# coding=utf-8


def group_forms(forms: list[str]) -> list[list[str]]:
    klassen = list(forms)

    groups = []
    while len(klassen) > 0:
        cur_klasse = klassen[0]
        if "/" in cur_klasse:
            cur_group = [elem for elem in klassen if elem.split("/")[0] == cur_klasse.split("/")[0]]
        elif "-" in cur_klasse:
            cur_group = [elem for elem in klassen if elem.split("-")[0] == cur_klasse.split("-")[0]]
        elif "." in cur_klasse:
            cur_group = [elem for elem in klassen if elem.split(".")[0] == cur_klasse.split(".")[0]]
        elif cur_klasse.isdigit():
            cur_group = [elem for elem in klassen if elem.isdigit()]
        elif not cur_klasse[0].isdigit():
            identifier = "".join([char for char in cur_klasse if not char.isdigit()])
            cur_group = [elem for elem in klassen if elem.startswith(identifier)]
        elif cur_klasse[0].isdigit():
            identifier = "".join([char for char in cur_klasse if char.isdigit()])
            cur_group = [elem for elem in klassen if elem.startswith(identifier)]
        else:
            cur_group = [cur_klasse]
        for elem in cur_group:
            if elem in klassen:
                klassen.remove(elem)
        groups.append(cur_group)
    return groups

def equal_dicts(d1, d2, ignore_keys):
    ignored = set(ignore_keys)
    for k1, v1 in d1.items():
        if k1 not in ignored and (k1 not in d2 or d2[k1] != v1) and k1 != "info":
            return False
    for k2, _ in d2.items():
        if k2 not in ignored and k2 not in d1 and k2 != "info":
            return False
    if set(d1["info"].split("; ")) == set(d2["info"].split("; ")):
        return True
    elif ("verlegt" in d1["info"]) or ("statt" in d1["info"]) or ("gehalten am" in d1["info"]):
        tmp_split1 = d1["info"].split(" ")
        tmp_split2 = d2["info"].split(" ")
        for i, word in enumerate(tmp_split1):
            if word.startswith("St."):
                tmp_st_word = f"{int((int(int(word[3:].replace(';', ''))) - 1)/2 + 1)}. Block{';' if word[-1:] == ';' else ''}"
                tmp_split1[i] = tmp_st_word
                tmp_split2[i] = tmp_st_word
        d1["info"] = ' '.join(tmp_split1)
        d2["info"] = ' '.join(tmp_split2)
        return True
    else:
        return False

def remove_duplicates(vplan_data):
    print(vplan_data)
    if len(vplan_data) < 2:
        return vplan_data
    new_vplan_data = []
    tmp_vplan_data = list(vplan_data)

    for i in range(0, len(tmp_vplan_data)):
        for j in range(0, len(tmp_vplan_data)):
            if (
                    # Um Duplikate zu verhindern
                    (not ("used" in tmp_vplan_data[i])) and 
                    (not ("used" in tmp_vplan_data[j]))
                ) and (
                    # Stunden sind maximal 1 voneinander entfernt
                    abs(int(tmp_vplan_data[i]["lesson"]) - int(tmp_vplan_data[j]["lesson"])) == 1
                ) and (
                    # Damit nicht z.B. Stunde 2 und 3 zusammengefasst werden können
                    (int(tmp_vplan_data[j]["lesson"]) < int(tmp_vplan_data[i]["lesson"]) and int(tmp_vplan_data[i]["lesson"]) % 2 == 0) or 
                    (int(tmp_vplan_data[i]["lesson"]) < int(tmp_vplan_data[j]["lesson"]) and int(tmp_vplan_data[j]["lesson"]) % 2 == 0)
                ):
                if equal_dicts(tmp_vplan_data[i], tmp_vplan_data[j], ["lesson", "begin", "end"]):
                    if tmp_vplan_data[i]["lesson"] < tmp_vplan_data[j]["lesson"]:
                        tmp_vplan_data[i]["lesson"] = str(int((int(tmp_vplan_data[i]["lesson"]) - 1)/2 + 1))
                        tmp_vplan_data[i]["end"] = tmp_vplan_data[j]["end"]
                        new_vplan_data.append(tmp_vplan_data[i])
                    else:
                        tmp_vplan_data[j]["lesson"] = str(int((int(tmp_vplan_data[j]["lesson"]) - 1)/2 + 1))
                        tmp_vplan_data[j]["end"] = tmp_vplan_data[i]["end"]
                        new_vplan_data.append(tmp_vplan_data[j])
                    tmp_vplan_data[i]["used"] = True
                    tmp_vplan_data[j]["used"] = True
    for i in range(0, len(tmp_vplan_data)):
        for j in range(0, len(tmp_vplan_data)):
            if ((not ("used" in tmp_vplan_data[i])) and (not ("used" in tmp_vplan_data[j]))) and (int(tmp_vplan_data[i]["lesson"]) - int(tmp_vplan_data[j]["lesson"]) == 1 or int(tmp_vplan_data[i]["lesson"]) - int(tmp_vplan_data[j]["lesson"]) == -1):
                tmp_vplan_data[i]["lesson"] = f'{int((int(tmp_vplan_data[i]["lesson"]) - 1)/2 + 1)} - 1'
                tmp_vplan_data[j]["lesson"] = f'{int((int(tmp_vplan_data[j]["lesson"]) - 1)/2 + 1)} - 2'
                new_vplan_data.append(tmp_vplan_data[i])
                new_vplan_data.append(tmp_vplan_data[j])
                tmp_vplan_data[i]["used"] = True
                tmp_vplan_data[j]["used"] = True
    for i in range(0, len(tmp_vplan_data)):
        if not "used" in tmp_vplan_data[i]:
            tmp_vplan_data[i]["lesson"] = f'{int((int(tmp_vplan_data[i]["lesson"]) - 1)/2 + 1)} - 1'
            new_vplan_data.append(tmp_vplan_data[i])
            tmp_vplan_data[i]["used"] = True

    sorted_data = sorted(new_vplan_data, key=lambda d: d['lesson'])
    return sorted_data