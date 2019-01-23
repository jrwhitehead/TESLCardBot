from bs4 import BeautifulSoup
import json, boto3, sys, os, time, csv, urllib.request, urllib, urllib.parse, requests, filecmp
from collections import OrderedDict

same = None

# # -*- coding: utf-8 -*-

S3_BUCKET_NAME = os.environ['S3_BUCKET_NAME']
AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']

print('card_fetcher# Started scraping cards from legends-decks.com.')

def load_card(path):
    ignore = ["played in", 
              "bbcode", 
              "soul summon", 
              "soul trap", 
              "unlocked in", 
              "expansion set", 
              "collectible", 
              "created by:", 
              "keywords"]
    replace = {"magicka cost": "cost"}    
    soup = BeautifulSoup(urllib.request.urlopen(path).read(), "html.parser")
    data = []
    table = soup.find('table')
    table_body = table.find('tbody')
    rows = table_body.find_all('tr')
    for row in rows:
        cells = row.findAll('td')
        output = []
        for i, cell in enumerate(cells):
            text = cell.text.strip()
            text_lower = text.lower()
            if i == 0:
                if text_lower in ignore:
                    break
                if text_lower in replace:
                    output.append(replace[text_lower])
                else:
                    output.append(text_lower)
            elif text:
                text = text.replace('\n', ' ').replace('\r', '').replace('\u201c', '\'').replace('\u201d', '\'').replace("\"", " ").replace("\u2019", "\'").replace("  ", " ")
                if output[0] == "race":
                    text = text_lower.replace(" ", "")
                if output[0] == "type":
                    text = text_lower
                    if text == "action":
                        data.append(["attack", "0"])
                        data.append(["health", "0"])
                output.append(text)
            elif cell.find_all('img'):
                if output[0] == "attributes":
                    cardAttributes = cell.find_all('img')[0].get('alt').title()
                    if len(cell.find_all('img')) == 2:
                        cardAttributes += '/'
                        cardAttributes += cell.find_all('img')[1].get('alt').title()
                    if (len(cell.find_all('img'))) == 3:
                        cardAttributes += '/'
                        cardAttributes += cell.find_all('img')[1].get('alt').title()
                        cardAttributes += '/'
                        cardAttributes += cell.find_all('img')[2].get('alt').title()
                    output.append(cardAttributes)
            else:
                output.append("")
        if output:
            if output[0] == "rarity":
                data.append(output)
                if output[1] == "Legendary - Unique":
                    output[1] = "Legendary"
                    data.append(["isunique", True])
                else:
                    data.append(["isunique", False])
            else:
                data.append(output)
    return data

def load_list(path):
    soup = BeautifulSoup(urllib.request.urlopen(path).read(), "html.parser")
    data = []
    table = soup.findAll('table')[1]
    table_body = table  
    rows = table_body.findAll('tr')
    for row in rows:
        cells = row.findAll('td')
        data.append(cells[1].find('a')['href'])
    return data
    
def custom_sort (to_sort):
  list1 = []
  list2 = []
  for el in to_sort:
    if el[0] in sorting_order:
      list1.append(el)
    else:
      list2.append(el)

  list1.sort(key=lambda v:sorting_order.index(v[0]))
  list2.sort()

  return list1+list2

sorting_order = [
  "name",
  "rarity",
  "isunique",
  "type",
  "attributes",
  "cost",
  "attack",
  "health",
  "race",
  "text"]

dict = []
for x in range(21):
    path = "https://www.legends-decks.com/cards/all/mana-up/"
    path += (str(x+1))
    path += "/list?f-collectible=both&f-set=all"
    print('card_fetcher# Started page',(x+1))
    for path2 in load_list(path):
        dict.append(OrderedDict(custom_sort(load_card(path2))))
    print('card_fetcher# Finished page',(x+1))
print('card_fetcher# Saving to cards.json.')
open("cards.json", "w").write(json.dumps(dict, indent=2, sort_keys=False))
#print("card_fetcher# Uploading cards.json to AWS.")
#s3 = boto3.resource('s3')
#s3.meta.client.upload_file('cards.json', S3_BUCKET_NAME, 'cards.json')
print('card_fetcher# All done for now. Going to Sleep.')
time.sleep(2)

################
# get cards.json from AWS and save as old-cards.json
#

print('downloader-9000 # Downloading cards.json from AWS.')
urllib.request.urlretrieve('http://teslcardscrapercardsdb.s3.amazonaws.com/cards.json', 'old-cards.json')
print('downloader-9000 # Finished downloading and saving cards.json as old-cards.json.')
time.sleep(2)


def compare_files(f1,f2):
    same = (filecmp.cmp(f1, f2, shallow=False))
    if same == False:
        print('compare # cards.json has changed.')
        print('compare # Proceeding to; upload cards.json, get missing card images from legends-decks and upload new card images to AWS.')
        os.system("python card_handler.py")
    else:
        print('compare # cards.json matches old cards.json.')
        print('compare # Nothing to do here.')
        print('compare # All done for now. Going to Sleep.')
        time.sleep(86400)

if __name__ == '__main__':
    compare_files('cards.json', 'old-cards.json')
