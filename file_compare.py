from bs4 import BeautifulSoup
import json, boto3, sys, os, time, csv, urllib.request, urllib, urllib.parse, requests, filecmp, re
from collections import OrderedDict

# # -*- coding: utf-8 -*-

S3_BUCKET_NAME = os.environ['S3_BUCKET_NAME']
AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']

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
    
def custom_sort(to_sort):
    sorting_order = ["name","rarity","isunique","type","attributes",
                    "cost","attack","health","race","text"]
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

def scrape_cards():
    ################
    # scrape all card details from legends-decks.com
    log('Started scraping cards from legends-decks.com.')
    dict = []

    #Get number of pages to scrape
    page = requests.get("https://www.legends-decks.com/cards/all/mana-up/1/list?f-collectible=both&f-set=all")
    page_soup = BeautifulSoup(page.content, 'html.parser')
    mydivs = page_soup.findAll("a", {"class": "pagin"})
    mydivs_string = str(mydivs)
    pages = re.findall("\d+\d+",mydivs_string)[0]
    int_pages = int(pages)
    log('There are {} pages to scrape.'.format(pages))

    #Scrape the card names from the number of pages identified to have cards from above code
    try:
        for x in range(int_pages):
            path = "https://www.legends-decks.com/cards/all/mana-up/"
            path += (str(x+1))
            path += "/list?f-collectible=both&f-set=all"
            log('Started page {}.'.format(x+1))
            for path2 in load_list(path):
                dict.append(OrderedDict(custom_sort(load_card(path2))))
            log('Finished page {}.'.format(x+1))
        log('Saving to cards.json.')
        open("cards.json", "w").write(json.dumps(dict, indent=4, sort_keys=False))
        log('Finished scraping all pages.')
    except:
        log('An error occured whilst scraping.')

def download_json_file():
    ################
    # get cards.json from AWS and save as old-cards.json

    log('Downloading cards.json from AWS.')
    urllib.request.urlretrieve('http://teslcardscrapercardsdb.s3.amazonaws.com/cards.json', 'old-cards.json')
    log('Finished downloading and saving cards.json as old-cards.json.')

def compare_files(f1,f2):
    same = (filecmp.cmp(f1, f2, shallow=False))
    if same == False:
        cards_size = (os.path.getsize(f1))
        old_cards_size = (os.path.getsize(f2))
        if old_cards_size > cards_size:
            log('Either something is wrong or cards have been nerfed.')
            log('The new cards.json is smaller than the old file.')
            log('Need to check what, if anything, has changed and upload nerfed/buffed cards')
            os.system("python card_handler.py")
        else:
            log('cards.json has changed.')
            log('Proceeding to; upload cards.json, get missing card images from legends-decks and upload new card images to AWS.')
            os.system("python card_handler.py")
    else:
        log('cards.json matches old cards.json.')
        log('Nothing for me to do here.')
        return

def log(msg):
    print('file_compare # {}'.format(msg))

if __name__ == '__main__':
    log('Starting..')
    download_json_file()
    scrape_cards()
    compare_files('cards.json', 'old-cards.json')
    sys.exit(0)
