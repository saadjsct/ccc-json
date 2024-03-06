from bs4 import BeautifulSoup
from bs4 import Tag
from urllib.request import urlopen
from pprint import pprint
import re
import os.path
import json

p_color= '993300'
kmala_color = '000000'

def is_paragraph_start(paragraph):
        spans = paragraph.find_all('span') 
        if len(list(spans)) < 2 : return False
        span = list(spans)[1]
        trimmed = span.text.replace("-", "")
        trimmed = trimmed.replace("–", "")
        trimmed = trimmed.replace(" ", "")
        trimmed = trimmed.replace("أ", "")
        trimmed = trimmed.replace("إ", "")
        trimmed = trimmed.replace("الله", "")
        trimmed = trimmed.replace("ـ", "")
        trimmed = trimmed.replace("‘", "")

        if trimmed.isnumeric():
                #if int(trimmed) == 995: import pdb; pdb.set_trace()
                return int(trimmed)
        else: return False

def is_kmala(paragraph):
        children = [child for child in paragraph.children]
        if children and type(children[0]) == type(paragraph) and children[0].has_attr("style"):
                if "color" in children[0]["style"] and not "color: #000000" in children[0]["style"]: return False
                elif len(list(children[0].find_all("b")) + list(children[0].find_all("strong"))) == len(list(children[0].children)):
                        return False
                else: return True
        else: return False

def is_kmala_blue(paragraph):
        p_text = paragraph.text
        children = [child for child in paragraph.children]
        if children and type(children[0]) == type(paragraph):
                if children[0].name == "strong" and children[0].find("span"):
                        if children[0].find("span").text == paragraph.text:
                                if children[0].find("span").has_attr("style"):
                                        if  "color: #0000ff" in children[0].find("span")["style"]:
                                                return True
        return False

def run_checks(paragraphs):
        # check length
        if len(paragraphs) < 2864:
                print("length check fails, length=" + str(len(paragraphs)))
        else:
                print("length check is ok")

        #check continutity
        nums = [num for num in paragraphs]
        nums.sort()
        redflag = 0

        for i, num in enumerate(nums[:-1]):
                #if num == 47:  import pdb; pdb.set_trace()
                if nums[i]+1 != nums[i+1]:
                        print("continuty faild at:") 
                        print(nums[i+1])
                        redflag = 1     
        if not redflag:
                print("continuty testing succeded")

paragraphs = {}
for i in range(0,25):
        #import pdb; pdb.set_trace()
        with open(r".\html-src\{}.htm".format(i), "r", encoding="utf-8") as f:
                html = f.read()
        html = html.replace(u'\xa0', u' ')

        soup =  BeautifulSoup(html, "html5lib") 
        plist = soup.find_all('p')
        last_num = 0
        for paragraph in plist:
                if is_paragraph_start(paragraph):
                        num = is_paragraph_start(paragraph)
                        paragraphs[num] = paragraph.text
                        paragraphs[num] = paragraphs[num].strip(" \n")
                        paragraphs[num] = re.sub("\d+\s?(-|–|_|ـ)\s?", "", paragraphs[num].strip(" \n"))
                        last_num = num
                        #if num == 1987: import pdb; pdb.set_trace()

                elif last_num and (is_kmala(paragraph) or is_kmala_blue(paragraph)):
                        paragraphs[last_num] += "\n" + paragraph.text
                        paragraphs[last_num] = paragraphs[last_num].strip(" \n")

        print("read page number {}".format(i))


# parse missing
lines = []
with open(r".\html-src\missing.txt", "r", encoding="utf=8") as f:
        lines = f.readlines()
last_num = 0
for line in lines:
        if line.strip(" \n").isnumeric():
                last_num = int(line.strip(" \n"))
                paragraphs[last_num]=""
        else:
                if paragraphs[last_num]:
                        paragraphs[last_num] += "\n"
                        paragraphs[last_num] += line.strip(" \n")
                else:
                        paragraphs[last_num] += line.strip(" \n")

# 3andena moshkela lw feh fakra belkamel zar2a
# zy 2004 w 1987
print("read missing")
run_checks(paragraphs)
# the json file where the output must be stored 
json_file = open("arabic-ccc.json", "w") 
json.dump(paragraphs, json_file, indent = 6) 
json_file.close() 


print("endofall")
import pdb; pdb.set_trace()
