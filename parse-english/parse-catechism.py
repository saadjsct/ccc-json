from bs4 import BeautifulSoup
from bs4 import Tag
from urllib.request import urlopen
from pprint import pprint
import re
import os.path
import json

#TODO Index Analyticus

upstream_base_url = "http://www.scborromeo.org/ccc/"
local_base_url = "./html-src/"
abbreviations_file = "./abbreviations.json"
global_footnotes = []

# load abbreviations
abbreviations = {}
with open(abbreviations_file) as f:
    abbreviations = json.load(f)

def download_page(url):
    # takes a generic url
    download_url = upstream_base_url + url
    page = urlopen(download_url)
    html = page.read().decode("utf-8", errors="ignore")
    with open(local_base_url + url, "w") as f:
        f.write(html)
    print("downloading " + url)

def is_part(tag):
    return tag.text.strip("\n").startswith("PART") or \
            tag.text.strip("\n").startswith("PROLOGUE")

def is_section(tag):
    return tag.text.strip("\n").startswith("SECTION")

def is_chapter(tag):
    return tag.text.strip("\n").startswith("CHAPTER")

def is_article(tag):
    return tag.text.strip('\n').startswith("ARTICLE")

def is_senior_paragraph(tag):
    return tag.text.strip('\n').startswith("Paragraph") or \
        tag.text.strip('\n').startswith("* Paragraph")

def is_roman_number(tag):
    text = tag.text.strip('\n* ')
    match = re.search(r'^[*]?[IVXLCDM]+[.]\s', text)
    if match: return True
    # manual upstream bug fix 
    if text == 'VII "BUT DELIVER US FROM EVIL"': return True 
    # AMEN and IN BRIEF are on the same level of roman numbers
    if text == '"AMEN"': return True
    if text == 'IN BRIEF': return True
    return False

def absolute_toc_level(tag):
    if is_part(tag): return 1
    elif is_section(tag): return 2
    elif is_chapter(tag): return 3
    elif is_article(tag): return 4
    elif is_senior_paragraph(tag): return 5
    elif is_roman_number(tag): return 6
    else: return 0

def is_paragraph(tag):
    # paragraph is an element with text that starts with number
    text = tag.text.strip("\n ")
    m = re.search("^[0-9]+\s", text)
    if m:
        return int(m.group().strip(" "))
    else: return False

def is_paragraph_group(tag, next_sibling):
    # paragraph group is an element that is all in bold and not toc_header
    # first check is not necessary as its below in the main function's if
    # one known exception to this is "I Am who I Am" so we need to check
    # that the next sibling is a paragraph
    return not absolute_toc_level(tag) \
            and tag.find("b") \
            and  tag.text.strip("\n *") == tag.b.text.strip("\n *") \
            and is_paragraph(next_sibling)

# def isolate_definitions(definitions):
#     isolated = []
#     for i, definition in enumerate(definitions):

#         # manually fix typos in upstream
#         # if definition == 'Cf.  57':
#         #     definition = "Cf. OCF 57"
#         # elif definition == "Cf.  20:1-17":
#         #     definition = "Cf. Ex 20:1-17"

#         verse_reg = r"(((([cC]f.? ?)|(PG))?([0-9\-:. §,/]*))+)$"
#         match = re.search(r"^" + verse_reg, definition)
#         if match:
#             if not isolated:
#                 print("found Broken ref")
#                 isolated.append(definition + " BRKNREF! ")
#                 continue
                
#             prevdef = isolated[-1]
#             prevmatch = re.search(verse_reg, prevdef)
#             end = prevdef.index(prevmatch.group(1).strip(' '))

#             complete = ""
#             if match.groups()[3]:
#                 complete = str(match.groups()[3]) + prevdef[:end] + \
#                     match.groups()[0].replace(str(match.groups()[3]), "")
#             else: 
#                 complete = prevdef[:end] + definition

#             isolated.append(complete)
#         else:
#             isolated.append(definition)
#     return isolated

def get_footnotes(soup):
    # paragraphs is the finished collection of paragraphs
    hr = soup.find("hr", attrs={"align": "LEFT"})
    if not hr: return []
    footnotes_tag = hr.next_sibling.next_sibling
    lines_list = footnotes_tag.text.strip('\n').split('\n')
    footnotes = []
    for line in lines_list:
        stripped = line.strip(". \n")
        if stripped == '': continue
        match = re.search('^(\d|l)*\s', stripped)
        ref = stripped[:match.end()-1]
        if ref == "l":
            ref = "1"
        def_ = stripped[match.end():]
        # defs = stripped[match.end():].split(";")
        # defs = [d.strip(" ") for d in defs]
        # isolated = isolate_definitions(defs)
        footnotes.append({"ref": ref, "definition": def_})
    return footnotes

def get_relevant_footnotes(tag, footnotes):
    sups = tag.find_all("sup")
    refs = [sup.text for sup in sups]
    relevant = [fn for fn in footnotes if fn['ref'] in refs]
    return relevant

def selector_function(tag):
    return tag.name == "p" or tag.name == "dl" or \
        (tag.name == "hr" and tag.has_attr("align") and
         tag["align"] == "LEFT")

def fix_page_of_119(html):
    str_119 = '<B><A HREF="javascript:openWindow(\'cr/119.htm\''
    index = html.find(str_119)
    fixed_html = html[:index] + "<P>\n" + html[index:]
    return fixed_html

def make_soup(page_url):
    html = ""
    with open(local_base_url + page_url, "r") as f:
        html = f.read()
    if page_url == 'p1s1c2a3.htm':
        # manually fix misformatting in 119
        html = fix_page_of_119(html) 

    return BeautifulSoup(html, "html5lib")

def decompose_tag(tag):
    decomposed = []
    strings = [s for s in tag.strings if s.strip("\n ") != ""]
    for string in strings:
        type_ = ""
        parent_name = string.parent.name
        if parent_name == "sup":
            type_ = "ref"
        elif parent_name == "i":
            type_ = "i"
        elif string.isnumeric():
            type_ = "p_num"
        else: type_ = "text"
        element_object = {
            "object_type": type_,
            "text": str(string.strip("\n "))
        }
        decomposed.append(element_object)
    return decomposed

def get_element_type(tag, lost_parents):
    parents = []
    if tag in lost_parents.keys():
        his_parent = lost_parents[tag]
        parents = [his_parent] + list(his_parent.parents)
    else:
        parents = list(tag.parents)

    if tag.find("dd") or "dl" in [t.name for t in parents]:
        return "description"
    else: return "normal"


def element_from_tag(tag, lost_parents):
    element = {
        "element_type": get_element_type(tag, lost_parents),
        "objects": decompose_tag(tag)
    }
    return element

def get_cross_references(tag):
    # if it doesn't have a["href"] return []
    # construct the cr link
    # if its not downloaded, download it.
    # construct the soup and parse it and return a list of numbers
    a_tag = tag.find(lambda e : e.name == "a" and e.has_attr("href"))
    if a_tag:
        href = a_tag["href"]
        match = re.search("\('(.*\.htm)'\)", href)
        if not match: return []
        cr_url = match.group(1)
        if not os.path.isfile(local_base_url + cr_url):
            print("couldn't find " + local_base_url + cr_url)
            download_page(cr_url)
        soup = make_soup(cr_url)
        a_tags = soup.find_all("a")
        cr = []
        for a in a_tags:
            text = a.text.strip("\n ")
            if text.isnumeric():
                cr.append(int(text))
        return cr
    else: return []

def scrap_page(page_url):
    # takes genric url (e.g produced by unique urls)
    if not os.path.isfile(local_base_url + page_url):
        download_page(page_url)

    soup = make_soup(page_url)
    footnotes = get_footnotes(soup)
    hr = soup.find("hr", attrs={"align": "LEFT"})
    siblings = soup.find_all(selector_function)
    if hr and (last := siblings.index(hr)):
        siblings = siblings[:last]
    paragraphs = []
    p_groups = []
    section_front = {"elements": [], "footnotes": [], "url": ""}
    ignored = []
    empty = []
    section_break = True # flag because sections reset parag. grouping
    lost_parents = dict()

    if page_url in  ["credo.htm", "command.htm"]:

        table = soup.find("table")
        section_front = {
                    "elements": [{"element_type": "chart",
                                "objects": [{"object_type": "html_table",
                                            "text": str(table)}]
                                  }],
                    "footnotes": [],
                    "cr": [],
                    "url": upstream_base_url + page_url
        }
        return paragraphs, p_groups, section_front, ignored, empty
    

    for i, sibling in enumerate(siblings):
        if not isinstance(sibling, Tag) or sibling.text.strip("\n") == "":
            empty.append(sibling)
            continue
        if sibling.name == "hr": break

        while sibling.find("p"):
            # keep record for kid's parent, before we separate them
            lost_parents[sibling.find("p")] = sibling
            sibling.find("p").replace_with("")

        if absolute_toc_level(sibling):
            # ignore toc headers
            ignored.append(sibling)
            section_break = True

        elif num := is_paragraph(sibling):
            # found new paragraph -> construct paragraph object
            paragraph = {
                "number" : num,
                "elements": [element_from_tag(sibling, lost_parents)],
                "url": upstream_base_url + page_url + "#" + str(num),
                "footnotes": get_relevant_footnotes(sibling, footnotes),
                "cr": get_cross_references(sibling)
            }
            paragraphs.append(paragraph)

            if len(p_groups) and not section_break:
                p_groups[-1]["range"][1] = num

        elif is_paragraph_group(sibling, siblings[i+1]):
            # alternative better solution to avoid using tags
            if range_start := is_paragraph(siblings[i+1]):
                # ranges include last paragraph
                p_group = {"range": [range_start, range_start],
                            "name": sibling.text.strip("\n *"),
                            "url": upstream_base_url + page_url,
                            "footnote": get_relevant_footnotes(sibling, footnotes)}
                p_groups.append(p_group)
                section_break = False

        elif len(paragraphs):
            #this is part of the last paragraph
            # append element to last paragraph's elements
            paragraphs[-1]["elements"].append(element_from_tag(sibling, lost_parents))
            relevant_footnotes = get_relevant_footnotes(sibling, footnotes)
            paragraphs[-1]["footnotes"].extend(relevant_footnotes)
        else:
            # if it's nothing, it's section_front
            # the whole thing sometimes is surrounded by dl
            # so if .find("p") remove it
            upstream_url = upstream_base_url + page_url
            section_front["url"] = upstream_url
            relevant = get_relevant_footnotes(sibling, footnotes)
            section_front["footnotes"].extend(relevant)
            section_front["elements"].append(element_from_tag(sibling, lost_parents))
            section_front["cr"] = []

    return paragraphs, p_groups, section_front, ignored, empty

def form_toc():
    toc_url = "ccc_toc2.htm"
    if not os.path.isfile(local_base_url + toc_url):
        download_page(toc_url)

    toc_html = ""
    with open(local_base_url + toc_url, "r") as f:
        toc_html = f.read()
    soup = BeautifulSoup(toc_html, "html5lib")

    toc = []
    unique_urls = []
    rows = soup.find_all("tr") 
    for row in rows[3:-1]: # excluding apos. letters and abbrev pages
        contents = [each for each in row.contents if isinstance(each, Tag)]
        if contents[0].text:
            prange = [int(each) for each in contents[0].text.split('-')]
            absolute_level = absolute_toc_level(contents[1])
        else:
            # here we handle the charts sections
            prange = [0, 0]
            absolute_level = 2

        if len(prange) == 1 : prange.append(prange[0])
        name = contents[1].text
        url = contents[1].find("a")["href"]
        heading = {
            "range": prange,
            "name": name,
            "absolute_level": absolute_level,
            "url": upstream_base_url + url,
        }
        toc.append(heading)
        if "#" not in url: unique_urls.append(url)

    unique_urls = list(set(unique_urls))
    return toc, unique_urls

def key_sort_paragraphs(p):
    return p["number"]

def range_start(e):
    return e["range"][0]

def range_end(e):
    return e["range"][1]

def get_toc_from_number(number, toc):
    # make another function: get youngest with url
    for i, e in enumerate(toc):
        if len(e["range"]) < 2: continue
        low = e["range"][0]
        high = e["range"][1]
        if number >= low and number <= high:
            return i, e

def what_is_missing(paragraphs):
    pnumber = 0
    missing = 0
    for i, p in enumerate(paragraphs):
        if p["number"] == pnumber +1:
            pnumber += 1
            continue
        else:
            print("\n\n")
            print("break at: " + str(pnumber + 1) + " - @ index " + str(i-1))
            print("jumped to " + str(p["number"]))
            i, toc_element = get_toc_from_number(paragraphs[i-1]["number"], toc)
            print("upstream page: " + toc_element["url"])
            print("\n")

            missing += p["number"] - pnumber + 1
            pnumber = p["number"]

    print ("missing ->>> " + str(missing) + "\n")
    return missing

def get_span(toc_element):
    return toc_element["range"][1] - toc_element["range"][0]

def get_youngest_from_url(toc, url):
    # gets upstream url and toc retern element and index in toc
    # de kda btget el oldest, da esm adeem
    parents = [heading for heading in toc if heading["url"] == url]
    parents.sort(key=get_span)
    youngest = parents[0]
    i = toc.index(youngest)
    return i, youngest

def inject_section_fronts(section_fronts, toc):
    # the charts should be injected here not separetly in a different function
    injected_entries = []
    for entry in toc:
        entry["section_front"] = {}
    for section_front in section_fronts:
        section_front_url = section_front["url"]
        i, entry = get_youngest_from_url(toc, section_front_url)
        entry["section_front"] = section_front
        section_front.pop("url") # i dont need url anymore after this point
        if not entry in injected_entries:
            injected_entries.append(entry)
    return injected_entries

def range_contains_range(range1, range2):
    return range1[0] <= range2[0] and range1[1] >= range2[1]

def merge_pgroups_and_toc(p_groups, toc):
    # modifies p_groups and toc. (total length 854)
    p_groups.sort(reverse=True, key=range_start)

    for entry in toc:
        entry["footnote"] = [] # dress toc as pg

    for p_group in p_groups:
        p_group["section_front"] = {} # dress pg as toc

        # add specific url to every p_group
        general_url = p_group["url"]
        p_group["url"] = general_url + "#" + str(p_group["range"][0])
        p_group["absolute_level"] = 7

        containing_entries = []
        for i, entry in enumerate(toc):
            if range_contains_range(entry["range"], p_group["range"]):
                containing_entries.append({"index": i, "entry": entry})

        containing_entries.sort(key = lambda e : get_span(e["entry"]))
        parent = containing_entries[0]
        toc.insert(parent["index"]+1, p_group)


toc, unique_urls = form_toc()

paragraphs = []
p_groups = []
section_fronts = []
ignored = []
empty = []

for url in unique_urls:
    data = list(scrap_page(url))
    paragraphs.extend(data[0])
    p_groups.extend(data[1])
    if data[2]["elements"]: section_fronts.append(data[2])
    ignored.extend(data[3])
    empty.extend([data[4]])

# modifies toc objects in place 
inject_section_fronts(section_fronts, toc)

paragraphs.sort(key=key_sort_paragraphs)
what_is_missing(paragraphs) # perfom continuity check

# dump to json file
merge_pgroups_and_toc(p_groups, toc)

# ready to dump
json_data = {"toc": toc, "paragraphs": paragraphs, "abbreviations": abbreviations}
json_file_name = "catechism.json"
with open(json_file_name, "w") as f:
    json.dump(json_data, f)
    print("dumped date to " + json_file_name)
import pdb; pdb.set_trace()

