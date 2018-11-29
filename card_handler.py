
# This script takes cards.json as input and uploads file to AWS.
#
# It also downloads all card images from Legends-decks.com and uploads them to AWS too.
# 
# The card bot now uses the cards.json and card images hosted on AWS thus not using Legends-decks.com
# bandwidth each time an image is accessed.
#
#
# # -*- coding: utf-8 -*-
"""
Created on Mon Apr 10 10:39:50 2017
@author: jersey
"""
from bs4 import BeautifulSoup
import urllib.request
import json, boto3, sys, os, time, csv, urllib.request, urllib, urllib.parse
from collections import OrderedDict

S3_BUCKET_NAME = os.environ['S3_BUCKET_NAME']
AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']

print("card.json_uploader# Uploading cards.json to AWS.")
s3 = boto3.resource('s3')
s3.meta.client.upload_file('cards.json', S3_BUCKET_NAME, 'cards.json', ExtraArgs={'ACL': "public-read", 'StorageClass': "REDUCED_REDUNDANCY"})
print('card.json_uploader# All done for now. Going to Sleep.')
time.sleep(5)

#
#
# This section takes the cards.json file as input and outputs a csv file of all card names.
#
print('json_csv_converter# Converting files to .csv')

def json2csv(file2convert):
    print(('json_csv_converter# Reading {}').format(file2convert))
    card_data = open(file2convert,"r")
    cards_parsed = json.load(card_data)

    file2convertcsv = os.path.splitext(file2convert)[0]
    file2convertcsv = file2convertcsv + '.csv'

    # open a file for writing
    output_card_data = open(file2convertcsv, 'w', newline='')

    # create the csv writer object
    csvwriter = csv.writer(output_card_data)

    count = 0

    for card in cards_parsed:
        name = ([cards_parsed[count]['name']])
        name = [item.replace('\n', '').replace('\r', '').replace('\u201c', '').replace('\u201d', '')
        .replace("\"", "").replace("\u2019", "").replace(" ", "").replace("[", "").replace("]", "")
        .replace("\"]", "").replace("[\"", "").replace("\'", "").replace("\"", "").replace(",", "").replace("-", "") for item in name]
        name = [item.lower() for item in name]
        csvwriter.writerow(name)
        count += 1
    print(('json_csv_converter# Writing output to {}').format(file2convertcsv))
    output_card_data.close()

json2csv('cards.json')
json2csv('old-cards.json')
print('json_csv_converter# All done. Going to sleep.')
time.sleep(2)

# This section find the difference between the csv files..
#
old = set((line.strip() for line in open('old-cards.csv')))
new = set((line.strip() for line in open('cards.csv')))

print('difference# Checking what\'s different and saving to diff.csv.')
with open('diff.csv', 'w') as diff:
    num_of_differences = 0
    for line in new:
        if line not in old:
            diff.write('{}\n'.format(line))
            num_of_differences += 1

print(('difference# There were {} new cards to add!').format(num_of_differences))
print('difference# All done. Going to sleep.')
time.sleep(2)
#
#
#
#
# This section takes the diff.csv file of card names as input and downloads the card images from legends-decks.com and uploads the images to AWS.
#
print('card_grabber_and_uploader# Reading diff.csv.')
count = 1

with open ('diff.csv', newline='') as csvfile:
    cardreader = csv.reader(csvfile, delimiter=',')
    for row in cardreader:
        url = ('http://www.legends-decks.com/img_cards/{}.png'.format(row[0]))
        split = urllib.parse.urlsplit(url)
        filenamePath = "cards/" + split.path.split("/")[-1]
        filename = split.path.split("/")[-1]
        urllib.request.urlretrieve(url, filename)
        print('card_grabber_and_uploader# This is card number:', count)
        print(('card_grabber_and_uploader# Saving file {} locally').format(filename))
        print(('card_grabber_and_uploader# Uploading {} to AWS.').format(filename))
        s3 = boto3.resource('s3')
        s3.meta.client.upload_file(filename, S3_BUCKET_NAME, filenamePath, ExtraArgs={'ContentType': "image/png", 'ACL': "public-read", 'StorageClass': "REDUCED_REDUNDANCY"})
        count += 1
print('card_grabber_and_uploader# All done. Going to sleep.')
time.sleep(86400)
