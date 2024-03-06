import json
import textwrap

json_file = "catechism.json"
org_file = "catechism.org"
global_footnotes = []

# w asasn mafesh moshkela deal breaker fel performance
# 5ally el performance a5er 7age hategy bel tweaking w enak te3rf eh el 7agat el monasba w ezay t7asenha. 2 ba3den kollaha kam sana w tgeb lab gded aw org mode nafso yettawar.
# el performance me7tag bs external tool lel search.
# w shwayet tweaking lel ta7arokat gowwa
# w dool hayeego bel tweaking bit by bit.
# w lw el multiple files ektashaft enno afdal ba3d shwaya 3ady.
# bs lazem tebtedy 3shan te3raf. da 7asab e7tyagak enta lel document de belzat
# mafehash egaba sahla. bs kol el options mota7a.
# lakn el afdal l7ad delwa2ty howwa aked el one file

# elly na2es fel org file
#TODO inpage notes that override readonly
# how to search with flexible patterns with regex


# moving around, you need to understand and learn the concept of marks. org mode automatically adds positions to mark ring when following ring.
# you can access previous marks by SPC r m,
# manually store marks in vim by vv
# make named evil marks (not in mark ring) by m<char> and go to this mark by `<char>

# elly na2es fel elements
#TODO el index
#TODO cross refrences
#TODO links le koll footnote
#TODO making property drawer holding needed info
# 3ayez tare2a abayn el paragragraph da feh cross refrences

def render_footnote(footnote):
    # footnotes should be local under each paragrph in a drawer
    # make a drawer holding info 
    string = "[fn:" + footnote["ref"] + "] "
    string += footnote["definition"] + "\n"
    return string

def render_object(element_object, p):
    object_type = element_object["object_type"]
    text = element_object["text"]
    if object_type == "p_num":
        if p["cr"]:
            return "⁘[[{0}][{1}]]".format(p["url"], text)
        else:
            return "[[{0}][{1}]]".format(p["url"], text)
    elif object_type == "i":
        return " /"+ text +"/"
    elif object_type == "ref":
        ## found new foot notes
        # 1) get its definition from paragraph footnotes by local_ref_number
        # 2) calculate global ref number = len(global_footnotes)
        # 3) render with the new global ref number
        # 4) append to global footnotes the definition with the global ref number
        # breakpoint()
        local_ref_number = int(text)
        footnote = [fn for fn in p["footnotes"] if int(fn["ref"]) == local_ref_number][0]
        global_ref_number = len(global_footnotes) + 1
        global_footnote = {
            "ref": str(global_ref_number),
            "definition": footnote["definition"][:]
        }
        p["global_footnotes"].append(global_footnote)
        global_footnotes.append(global_footnote)
        return " [fn:{}]".format(global_ref_number)
        # return " [fn:{}]".format(local_ref_number)
    
    elif object_type == "text":
        return " " + text
    elif object_type == "html_table":
        return text

# this for now ignores section elements
def render_paragraph(p):
    p["global_footnotes"] = []
    # takes a paragraph object {paragraph and or section}
    plevel = 8 
    string = ""
    if "number" in p.keys():
        # if its numbered. make heading and url for it
        string = plevel*"*" + " " + str(p["number"])

    for element in p["elements"]:
        string += "\n"
        if element["element_type"] == "chart":
            string += "#+BEGIN_EXPORT html\n"

        if element["element_type"] == "description":
            string += "#+BEGIN_QUOTE\n"

        for element_object in element["objects"]:
            string += render_object(element_object, p)

        if element["element_type"] == "chart":
            string += "\n#+END_EXPORT"

        if element["element_type"] == "description":
            string += "\n#+END_QUOTE"
        string += "\n"

    # if len(p["footnotes"]) != len(p["global_footnotes"]): breakpoint()
    if p["cr"] or p["footnotes"]:
        string += ":refs:\n"
    if p["cr"]:
        string += "cr: "
        for i, pnum in enumerate(p["cr"]):
            string += "[[*{0}][{0}]]".format(pnum)
            if i == len(p["cr"]) - 1 : string += ". "
            else: string+= ", "
        string += "\n\n"
    if p["footnotes"]:
        for global_footnote in p["global_footnotes"]:
            string += render_footnote(global_footnote)
    if p["cr"] or p["footnotes"]:
        string += ":end:\n"
    string += "\n"
    return string

def render_heading(entry):
    string = entry["absolute_level"]*"*" + " " + entry["name"] + "\n"
    if entry["section_front"]:
        string += render_paragraph(entry["section_front"])

    if entry["footnote"]:
        string += render_footnote(entry["footnote"][0]) + "\n "
    return string

catechism = {}
with open(json_file) as f:
    catechism = json.load(f)

toc = catechism["toc"]
paragraphs = catechism["paragraphs"]
abbreviations = catechism["abbreviations"]

org_string = ""
for i, entry in enumerate(toc):

    if entry["range"] == [0, 0]: continue
    heading_string = render_heading(entry)
    org_string += heading_string

    entry_pset = {i for i in range(entry["range"][0], entry["range"][1]+1)}
    exclusive_pset = entry_pset.copy()
    for sibling in toc[i+1:]:
        if sibling["range"] == [0, 0]: continue

        sibling_pset = {i for i in range(sibling["range"][0], sibling["range"][1]+1)}
        if entry_pset.issuperset(sibling_pset):
            exclusive_pset.difference_update(sibling_pset)
        else: break

    if exclusive_pset:
        for i in range(min(exclusive_pset), max(exclusive_pset) + 1):
            org_string += render_paragraph(paragraphs[i-1])

# lastly, render global footnotes in the footnotes section
# org_string += "* footnotes \n\n"
# for footnote in global_footnotes:
#     org_string += render_footnote(footnote)

org_string += "# local variables:\n# eval: (catechism-eval)\n# end:\n"

with open(org_file, "w") as f:
    f.write(org_string)

