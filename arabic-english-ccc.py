import re
import json
import compress_json
from pprint import pprint

arabic = {}
with open(r".\parse-arabic\arabic-ccc.json") as f:
    arabic = json.load(f)

english_mad_full = {}
english_mad = []
toc = []
abbreviations = {}
with open(r".\parse-english\catechism.json") as f:
    english_mad_full = json.load(f)

english_mad= english_mad_full["paragraphs"]
toc = english_mad_full["toc"]
abbreviations = english_mad_full["abbreviations"]

english_sane = {}

def to_sup(s):
    sups = {
        '0': '\u2070',
        '1': '\u00b9',
        '2': '\u00b2',
        '3': '\u00b3',
        '4': '\u2074',
        '5': '\u2075',
        '6': '\u2076',
        '7': '\u2077',
        '8': '\u2078',
        '9': '\u2079'
    }
    return ''.join(sups.get(char, char) for char in s)

# Example usage:
#number = '0123'
#superscript_number = to_sup(number)
#print("hello" + superscript_number + "this is")

for p_mad in english_mad:
    p_num = p_mad["number"]
    english_sane[p_num] = ""
    for element in p_mad["elements"]:
        for object in element["objects"]:
            if object["object_type"] == "text":
                english_sane[p_num] += object["text"]
            elif object["object_type"] == "ref":
                english_sane[p_num]  += to_sup(object["text"])
            elif object["object_type"] == "i":
                english_sane[p_num]  += " " + to_sup(object["text"]) + " "
            else: continue
        english_sane[p_num] += "\n"
    english_sane[p_num] = english_sane[p_num].replace("\xa0","")
    english_sane[p_num] = english_sane[p_num].strip(" \n")


# ana 3ayez dict of int keys equal number of paragraph
# el value bta3t el dict da hya list mn two
# value[0] da n7ot fe bas text el 3araby
# value[1] da n7ot fe dict mokawan mn text, footnotes, cr

english = {}
for i in range(1,2866):
    english[i]= {"text":"", #English text
                "footnotes":[], #english footnotes and difinitions
                "cr":[] #cross references
                }
    english[i]["text"] = english_sane[i] #sane dict btbtdy mn 1
    english[i]["footnotes"] = english_mad[i-1]["footnotes"]
    english[i]["cr"] = english_mad[i-1]["cr"]

# json_file = open("arabic-english-ccc.json", "w") 
# json.dump(ccc, json_file, indent = 6) 
# json_file.close() 

#parse toc translation
lines=[]
with open("toc-translation.txt", "r", encoding="utf=8") as f:
    lines = f.readlines()

def condition(name, toc_element):
    return name.strip(" \n") == toc_element["name"]

for i, line in enumerate(lines):
    if i%2 == 0: # english lines
        matches = [e for e in toc if condition(line, e)]
        match_index = toc.index(matches[0])
        toc[match_index]["arabicName"] = lines[i+1].strip(" \n")
    else: continue

# law mafesh element numeric da 3enwan kbeer


# fix missing in toc semi-manually
for entry in toc:
    if "arabicName" not in entry :
        if entry["name"] == 'IN BRIEF':
            entry["arabicName"] = "بإيجاز"
        if entry["name"] == "Faith":
            entry["arabicName"] = "الإيمان"
        if entry["name"] == "Hope":
            entry["arabicName"] = "الرجاء"
        if entry["name"] == "Charity":
            entry["arabicName"] = "المحبة" 
        if entry["name"] == "THE UNIVERSAL CALL TO PRAYER":
            entry["arabicName"] = "الدعوة الشاملة للصلاة"


arabic_list = [{"pnum": -1, "date": "first element is not a paragraph so that index would match pnum"}]
for (key, value) in arabic.items():
    arabic_list.append({"pnum": int(key), "data":value})

english_list = [{"pnum": -1, "date": "first element is not a paragraph so that index would match pnum"}]
for (key, value) in english.items():
    english_list.append({"pnum": int(key), "data":value})

def sort_on_pnum(item):
    return item["pnum"]
arabic_list.sort(key=sort_on_pnum)
english_list.sort(key=sort_on_pnum)

for i, entry in enumerate(toc):
    entry["key"] = i

# fix error upstrem in toc page of stborromeo
toc[259]["range"] = [680, 682]

# calculate pages
pages = ["toc", [1, 25]]
last_end = 25
for (i,e) in enumerate(toc):
    if e["name"] == "IN BRIEF":
        pages.append([last_end+1, e["range"][1]])
        last_end = e["range"][1]

# fix manually at part-break
pages[34] = [1020, 1065]
pages[35] = [1066, 1112]
pages[47] = [1680, 1690]
pages = pages[:48] + [[1691, 1715]] + pages[48:]


#fix toc manually
#[82, 383, 773, 778]
toc[82]["absolute_level"] = 7
toc[383]["absolute_level"] = 6
toc[773]["absolute_level"] = 7
toc[778]["absolute_level"] = 7

arabic_list[25]["data"] = arabic_list[25]["data"][:413] 
toc[64]["arabicName"] = "الإيمان بالله وحده"



compress_json.dump(arabic_list, r".\compressed_json_data\arabic-ccc.json.gz")
compress_json.dump(english_list, r".\compressed_json_data\english-ccc.json.gz")
compress_json.dump(toc, r".\compressed_json_data\toc-ccc.json.gz")
compress_json.dump(pages, r".\compressed_json_data\pages-ccc.json.gz")



def wareny(num):
    print("-------------------------------")
    print(arabic[str(num)])
    print(english[num]["text"])
 
import pdb; pdb.set_trace()