import re
import pdb
import json
import compress_json
from pprint import pprint

# every line is an object
# make the following functions:
# extract_pnums
# extracts_refs
# extract_names
# kol object momken yezhar feh el talata
# make the following global variables
# current letter used to append objects to letter
# current_parent, current_child, current_grand_child. those will hold object itself after constructing and appending
# make a function that takes the three currents and return adress to put in the object

def extract_pnums(line):
    number_parts = re.findall(r"[0-9]{1,4}-?[0-9]{0,4}", line)
    return number_parts

def extract_refs(line):
    match = re.search(r" ر:? ", line)
    if match:
        last_span = match.span()[1]
        refs_string = line[last_span:]
        return refs_string.split("، ")
    else:
        return []
    
def extract_name(line):
    ref_match = re.search(r" ر:? ", line)
    num_match = re.search(r"[0-9]{1,4}-?[0-9]{0,4}", line)
    up_to = -1
    name = ""
    if num_match:
        up_to = num_match.span()[0]
        name = line[:up_to]
    elif ref_match:
        up_to = ref_match.span()[0]
        name = line[:up_to]
    else:
        name = line
    name = name.replace(" ف ", "")
    # name = re.sub(r":\s?*$", "", name)
    return name.strip("#;،: \n؛")

file_lines =[]
with open(r".\full_written_input.txt", "r", encoding="utf-8") as f:
    file_lines = f.readlines()

lines = []
for file_line in file_lines:
    if file_line.strip(" \n") != "" and not re.search(r"ص\s?[0-9]{3,4}\s?", file_line):
        lines.append(file_line.strip(" \n.;؛:"))

ar_index = {}
current_letter = ""
current_hash_occurences = 1
last_hash_occurences = 1 

for line in lines:
    # print(f"------{line}--------")
    if line.startswith("حرف"):
        current_letter = line[-1]
        ar_index[current_letter] = []
        levels = []
    else: 

        object = {}
        object["name"] =  extract_name(line)
        pnums =  extract_pnums(line)
        refs = extract_refs(line)
        if pnums: object["paragraphs"] = pnums
        if refs: object["refs"] = refs 

        # kol el 7alat:
        # 1) mask 1 hash append it to letter
        # 2) mask 0 hash ba3d el wa7ed hash -> append it to parent
        # 3) mask 2 hash -> append it to parent
        # 4) mask 0 hash ba3d 2 hash -> append it to child 
        # 5) mask 3 hash -> append it to child
        # 6) mask 0 hash ba3d 3 hash -> append it to grand child

        current_hash_occurences = line.count('#')

        if current_hash_occurences:
            object["children"] = []
            if current_hash_occurences == 1 : # append it to letter
                ar_index[current_letter].append(object)
                last_hash_occurences = 1
            elif current_hash_occurences == 2: # append it to parent
                ar_index[current_letter][-1]["children"].append(object)
                last_hash_occurences = 2
            elif current_hash_occurences == 3: # appent it to child
                ar_index[current_letter][-1]["children"][-1]["children"].append(object)
                last_hash_occurences = 3
        else:
            if last_hash_occurences == 1:
                ar_index[current_letter][-1]["children"].append(object)
            elif last_hash_occurences == 2:
                ar_index[current_letter][-1]["children"][-1]["children"].append(object)
            elif last_hash_occurences == 3:
                ar_index[current_letter][-1]["children"][-1]["children"][-1]["children"].append(object)

                



out_file = open("arabic_index.json", "w", encoding="utf-8") 
json.dump(ar_index, out_file)
out_file.close() 
compress_json.dump(ar_index, r"..\compressed_json_data\arabic_index.json.gz")


pdb.set_trace()
