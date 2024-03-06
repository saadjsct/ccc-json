from bs4 import BeautifulSoup
from bs4 import Tag
from urllib.request import urlopen
from pprint import pprint
import re
import json
import compress_json

# merge both in one file

index_en = []
with open(r".\index full.txt", "r", encoding="utf-8") as f:
    index_en = f.readlines()



def calc_ind_level(string):
    count = len(string) - len(string.lstrip(" "))
    if count == 0:
        return 1
    elif count == 8:
        return 2
    elif count == 16:
        return 3
    else:
        return -1

def append_topic_as_child_of_last_parent(data, topic):
    if  "children" in data[-1].keys():
        data[-1]["children"].append({"name": topic})
    else:
        data[-1]["children"] = [{"name": topic}]

def append_topic_to_1st_subparent(data, topic):
    if "children" in data[-1]["children"][-1].keys():
        data[-1]["children"][-1]["children"].append({"name": topic})
    else:
        data[-1]["children"][-1]["children"] = [{"name": topic}]

def append_topic_to_2nd_subparent(data, topic):
    if "children" in data[-1]["children"][-1]["children"][-1].keys():
        data[-1]["children"][-1]["children"][-1]["children"].append({"name": topic})
    else:
        data[-1]["children"][-1]["children"][-1]["children"] = [{"name": topic}]


def append_data_to_parent(data_list, data_type, data):
    if data_type in data_list[-1].keys():
        data_list[-1][data_type].append(data)
    else:
         data_list[-1][data_type] = [data]

def append_data_to_child_of_parent(data_list, data_type, data):
    if data_type in data_list[-1]["children"][-1].keys():
        data_list[-1]["children"][-1][data_type].append(data)
    else:
         data_list[-1]["children"][-1][data_type] = [data]

def append_data_to_child_of_1st_subparent(data_list, data_type, data):
    if data_type in data_list[-1]["children"][-1]["children"][-1].keys():
        data_list[-1]["children"][-1]["children"][-1][data_type].append(data)
    else:
         data_list[-1]["children"][-1]["children"][-1][data_type] = [data]

def append_data_to_child_of_2nd_subparent(data_list, data_type, data):
    if data_type in data_list[-1]["children"][-1]["children"][-1]["children"][-1].keys():
        data_list[-1]["children"][-1]["children"][-1]["children"][-1][data_type].append(data)
    else:
        data_list[-1]["children"][-1]["children"][-1]["children"][-1][data_type] = [data]

def append_data_to_last_topic(data_list, last_level, data_type, data):
        if last_level == 0:
            append_data_to_parent(data_list, data_type, data)
        if last_level == 1:
            #append number to last parent's paragraphs
            append_data_to_child_of_parent(data_list,  data_type, data)
        elif last_level == 2:
            #append number to last 1st subparent paragraphs
                append_data_to_child_of_1st_subparent(data_list,  data_type, data)
        elif last_level == 3:
            #append number to last 1st subparent paragraphs
            append_data_to_child_of_2nd_subparent(data_list,  data_type, data)

def remove_unmatched_parenth(text):
    if text.count('(') != text.count(')'):
        rtext = re.sub('\(|\)', '', text)
        return rtext
    else: return text


def parse_page(page_letter):
    local_base_url = r".\html_src\_"
    file_text = ""
    with open( local_base_url + page_letter + ".htm", "r") as f:
            file_text = f.read()

    soup = BeautifulSoup(file_text, "html5lib")

    start = soup.find('a', attrs = {'name' : True}) # first parent
    see_flag = False
    see_text = ""
    last_level = 0   # 0-1-2-3
    inline = False
    page_data = [{"name": start["name"]}]

    #PAGE
    #0
    #0:
    #   1
    #   1
    #   1
    #0:
    #   1
    #   1:
    #       2
    #       2:
    #            3
    #            3
    #   1
    #0

    for e in start.next_siblings:
        if e.name == "b" or not str(e).strip(" \n., ;( )"):
            if "\n" in str(e): inline = False
            continue

        if e.name == "a" and e.has_attr("name") and e.next_sibling.name == "b":
            # found bold parent
            # lazem nzawd el check 3al bold 3shan feh subparents b name
            see_flag=False
            inline = False
            current_topic = e["name"]
            page_data.append({"name": current_topic})
            last_level= 0

        elif e.name == "i":
            # set the see flag for next sibling
            see_flag=True
            see_text= e.text
            if ("words" in see_text):
                index = see_text.find("words")
                append_data_to_last_topic(page_data, last_level-1 if not (last_level-1 < 0) else 0, "refs", see_text[index:])
    
        elif str(type(e)) == "<class 'bs4.element.NavigableString'>":
            # found new topic
            see_flag=False
            inline = False
            topics =  str(e).strip("\n").lstrip(")").split("\n")
            topics = [t for t in topics if t.strip(" \t\n") != ""]
            for topic in topics:
                ind_level = calc_ind_level(topic)
                topic = topic.strip(" \t\n., ;") # strip w naddaf b3d mat-calculate el indentation
                topic = remove_unmatched_parenth(topic)
                topic = topic.strip(" \t\n., ;") # strip w naddaf b3d mat-calculate el indentation
                if ind_level == 1:
                    append_topic_as_child_of_last_parent(page_data, topic)
                    last_level = ind_level
                    # append 3al parent

                elif ind_level == 2:
                    # append 3ala awel subparent
                    append_topic_to_1st_subparent(page_data, topic)
                    last_level = ind_level

                elif ind_level == 3:
                    # append 3ala tany subparent
                    append_topic_to_2nd_subparent(page_data, topic)
                    last_level = ind_level

        elif e.name == "a" and e.text.replace("-", "").isnumeric():
            append_data_to_last_topic(page_data, last_level, "paragraphs", e.text)
            inline = True

        elif see_flag and  e.text != see_text:
            if e.text.strip(' \n') == '': continue
            if inline:
                append_data_to_last_topic(page_data, last_level, "refs", e.text)
            else:
                append_data_to_last_topic(page_data, last_level-1 if not (last_level-1 < 0) else 0, "refs", e.text)

    return page_data
        
letters = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "qr", "s", "t", "u", "v", "wxyz"]

index_data = {}
for letter in letters:
    index_data[letter] = parse_page(letter)

# pprint(index_data)

print("no errors, we finished")

del(index_data["h"][15])
del(index_data["o"][6])

# by this stage we have the full english index structured

out_file = open("english_index.json", "w", encoding="utf-8") 
json.dump(index_data, out_file)
out_file.close() 
compress_json.dump(index_data, r"..\compressed_json_data\english_index.json.gz")

import pdb; pdb.set_trace()
 









# index_ar_ai =[]
# with open(r"C:\Users\saads\Desktop\catechism\arabic-english-catechism\Ai index\index full.en.ar.txt", "r", encoding="utf-8") as f:
#     index_ar_ai = f.readlines()

# 5od kol line fel english w 7ot warah el corresponding arabic removing white line
# w7ot el etnen fe list tanya w ektb el list fe file esmo merged
# index_merged_ai = []
# for i, line in enumerate(index_en):
#     if line == "\n": #empty line
#         continue
#     else :
#         ar_line = index_ar_ai[i]
#         index_merged_ai.append(line)
#         index_merged_ai.append(ar_line)

# with open(r"C:\Users\saads\Desktop\catechism\arabic-english-catechism\Ai index\index full.merged.ai.txt", "w", encoding="utf-8") as f:
#     for line in index_merged_ai:
#         f.write(line + "\n")


# ba2olak eh ana haparse al wake3 ashal

# download all index

# list mn 7rof 
# fe kol 7arf list mn el parents
# fe kol parent list (a2al 7aga see)
# lw 3andy level2 heading hyb2a mwgod gowwa el parent
# bs howwa nafso list
# max level2 heading



# the file of the translation we well use to emped transtations to this structure
# el render bta3 el 3arby hayklefak bs el search lelparent name
# 7awel kol parent yb2a leh targama mo5talefa 7atta lw ben qosen 3shan t7afez 3al structer

            

# file_text = ""
# with open(r"C:\Users\saads\Desktop\catechism\arabic-english-catechism\Ai index\index_translation_input.txt", "r", encoding="utf=8") as f:
#             file_text = f.readlines()

# translation_list = []
# last_i = -1
# for i,line in enumerate(file_text):

#     line = line.strip(" \n")
#     if line.strip(" \n") == "" : continue
#     if i == last_i+3: continue
#     # sparate see
#     see_index = line.find("See ") if line.find("See ") != -1 else line.find("see ")
#     if ("see God" in line and not "(see God" in line) or "Pharisee" in line: see_index = -1
#     if  see_index != -1 and see_index != 0:
#         before_see = line[0:see_index]
#         after_see = line[see_index:-1]
#         arabic_line = file_text[i+3].strip('\n')
#         arabicSee_index = arabic_line.find("أنظر")
#         if arabicSee_index == -1: 
#             arabicSee_index = arabic_line.find("انظر")
#         arabic_before_see = arabic_line[:arabicSee_index]
#         arabic_after_see = arabic_line[arabicSee_index:]
#         before_see = re.sub(" ?[0-9]?-?[0-9]+,?،?", "", before_see)
#         arabic_before_see = re.sub(" ?[0-9]?-?[0-9]+,?،?", "", arabic_before_see)

#         arabic_before_see = remove_unmatched_parenth(arabic_before_see).strip(" ’.,،:")
#         arabic_after_see = remove_unmatched_parenth(arabic_after_see).strip(" ’.,،:")
#         after_see = remove_unmatched_parenth(after_see).strip(" ’.,،:")
#         before_see = remove_unmatched_parenth(before_see).strip(" ’.,،:")
#         translation_list.append(before_see)
#         translation_list.append(arabic_before_see)
#         translation_list.append(after_see)
#         translation_list.append(arabic_after_see)
#         last_i= i
#         continue

#     line_to_append = re.sub(" ?[0-9]?-?[0-9]+,?،?", "", line).strip(" ’,،:")
#     translation_list.append(line_to_append)

# def get_translation_list_from_input():
#     # heyya de elly hatet8ayyar, hanekteb el file el tany bnafs el format
    
#     lines = []
#     with open(r"C:\Users\saads\Desktop\catechism\arabic-english-catechism\Ai index\index_translation_old_final_output_as_input.txt", "r", encoding="utf=8") as f:
#                 lines = f.readlines()

#     translation_list = [] # ovveriding old translation list
#     for (i,line) in enumerate(lines):
#         if i%2 == 1 or i == len(lines)-1: continue ## not interested in arabic (on even)
#         translation_list.append({"name": line.strip(" \n"), "arabicName": lines[i+1].strip(" \n")})
#     return translation_list

# translation_list = get_translation_list_from_input()

# def get_translation(english_string, parents_names = []):
#     search_list = list(reversed(parents_names)) + [english_string] 
#     pointer = 0
#     for si in search_list: 
#         # import pdb; pdb.set_trace()
#         # if english_string == "Christ, the Word of God": import pdb; pdb.set_trace()
#         for (i,t) in enumerate(translation_list[pointer:]):
#             if t["name"] == si:
#                 pointer += i
#                 break
#     if pointer != 0 or english_string == "Abandonment": 
#         return translation_list[pointer]["arabicName"]
#     else:
#         print(f"obba mal2etsh el translaton l {english_string}")
#         return ""


# translation_dict = {}
# for i, l in enumerate(translation_list):
#     #if l in translation_dict.keys() and l[0:1].isupper():
#     #     print( l + '\n' + translation_list[i+1] + '\n')        
#     translation_dict[l["name"]] = l["arabicName"]

# for letter in index_data:
#     for parent in index_data[letter]:
#         arabic_translation = get_translation(parent["name"])
#         if arabic_translation:
#             parent["arabicName"] = arabic_translation
#         else:
#             print()
#             print(f"parent is absent: {parent['name']}")
#             print("-----------info-----------")
#             print(f"child of: {parent['name']}")

#             print()
#         if "children" in parent.keys():
#             for child in parent["children"]:
#                 arabic_translation = get_translation(child["name"], [parent["name"]])
#                 if not arabic_translation:
#                     print()
#                     print()
#                     print("this child has no translation")
#                     print(f"{child['name']}")
#                     print("-----------info-----------")
#                     print(f"child of: {parent['name']}")
#                     print(child)
#                 else:
#                     child["arabicName"] = arabic_translation

#                 if "children" in child.keys():
#                     for grandchild in child["children"]:
#                         arabic_translation = get_translation(grandchild["name"], [child["name"], parent["name"]])
#                         if not arabic_translation:
#                             print()
#                             print()
#                             print("")
#                             print("this grandchild has no translation")
#                             print(f"{grandchild['name']}")
#                             print("-----------info-----------")
#                             print(f" child of: {child['name']}")
#                             print(f" grandchild of: {parent['name']}")
#                         else:
#                             grandchild["arabicName"] = arabic_translation

#                         if "children" in grandchild.keys():
#                             for grandgrandchild in grandchild["children"]:
#                                 arabic_translation = get_translation(grandgrandchild["name"], [grandchild["name"], child["name"], parent["name"]])
#                                 if not arabic_translation:
#                                     print()
#                                     print(f"didn't find translation of grandgrand child:\n {grandgrandchild['name']}")
#                                     print("-----------info-----------")
#                                     print(f"child of: {grandchild['name']}")
#                                     print(f"grandchild of: {child['name']}")
#                                     print(f"grandgrandchild of: {parent['name']}")
#                                     print(grandgrandchild)
#                                 else:
#                                     grandgrandchild["arabicName"] = arabic_translation

# def deconstruct_complex_ref(ref):
#     splitted = re.split(r'(\:|\,)', ref)
#     finished = [s.strip(":, ") for s in splitted if s.strip(":, ") != ""]
#     return finished

# def get_new_refs(parent):
#     # print(f"------------------- found refs of {parent["name"]}")
#     new_refs=[]
#     for ref in parent["refs"]:
#         if ref in translation_dict.keys():
#             # print(f"- [{ref}] with direct translation {translation_dict[ref]}")
#             new_refs.append({"refName": ref, "arabicRefName": translation_dict[ref]})
#         else:
#             if ":" in ref or "God, " in ref: # it is complex ref
#                 deconstructed = deconstruct_complex_ref(ref)
#                 complex_ref = []
#                 for (i,ref_part) in enumerate(deconstructed):
#                     if ref_part in translation_dict.keys():
#                         # print (f"found ref part no{i} direct translation: {ref_part}")
#                         complex_ref.append({"refPartName": ref_part, "refPartArabicName": translation_dict[ref_part]})
#                     else:
#                         print(f"------------ no translation of ref part in parent {parent['name']}")
#                         print (f"no translation for ref part '{ref_part}' it is no#{i}")
#                         print(f"original ref was'{ref}'")
#                         print(f"after deconstruction it was'{deconstructed}'")
#                 new_refs.append(complex_ref)
#             else: 
#                 print(f"------------ no translation of ref in parent {parent['name']}")
#                 print(f"- [{ref}] didn't find translation")
#     return new_refs

#imped ref translations
# for letter in index_data:
#     for parent in index_data[letter]:
#         if "refs" in parent.keys():
#             parent["refs"] = get_new_refs(parent)
#         if "children" in parent.keys():
#             for child in parent["children"]:
#                 if "refs" in child.keys():
#                     child["refs"] = get_new_refs(child)
#                 if "children" in child.keys():
#                     for grandchild in child["children"]:
#                         if "refs" in grandchild.keys():
#                             grandchild["refs"] = get_new_refs(grandchild)
#                         if "children" in grandchild.keys():
#                             for grandgrandchild in grandchild["children"]:
#                                 if "refs" in grandgrandchild.keys():
#                                     print()
#                                     #print()
#                                     #print(f"----------refs of {parent["name"]} >>> {child["name"]} >> {grandchild["name"]}-------------")
#                                     grandgrandchild["refs"] = get_new_refs(grandgrandchild)
#                                     print()


# 3ayzen n7ot fel index_data key esmo arabic
# feh dictionary mn kol 7arf arabic l list of dict 7arf english w index lel parent
# b7es enny lkol 7arf arabic a2dar awsal lel objects elly hatrender bel 7arf el english wel index bta3 el parent gowwa el 7arf el english

# def arabic_starts_with(string, letter):
#     string = string.strip(" \n")
#     return string.startswith(letter) or (string.startswith("ال") and string[2] == letter)
                      
# def construct_arabic_letters_dict():
#     arabic_letters = ["أ", "ب", "ت", "ث", "ج", "ح", "خ", "د", "ذ", "ر", "ز", "س", "ش", "ص", "ض", "ط", "ظ", "ع", "غ", "ف", "ق", "ك", "ل", "م", "ن", "ه", "و", "ي"]
#     arabic_map = {}
#     for arabic_letter in arabic_letters:
#         arabic_map[arabic_letter] = []
#         for english_letter in index_data.keys():
#             for (i,parent) in enumerate(index_data[english_letter]):
#                 if arabic_starts_with(parent["arabicName"], arabic_letter) or arabic_letter=="أ" and arabic_starts_with(parent["arabicName"], "آ"):
#                     arabic_map[arabic_letter].append({"letter": english_letter, "index": i})
#     return arabic_map

# arabic_map = construct_arabic_letters_dict()
# index_data["arabic_map"] = arabic_map


# generate working file 
# I need a file


# with open(r"C:\Users\saads\Desktop\catechism\arabic-english-catechism\Ai index\new_translation.txt", "w", encoding="utf-8") as f:
#     for letter in index_data.keys():
#         if letter == "arabic_map": break
#         for p in index_data[letter]:
#             f.write(p["name"])
#             f.write("\n\n")

