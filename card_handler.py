
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
import json, boto3, sys, os, time, csv, urllib.request, urllib, urllib.parse, re
#from collections import OrderedDict
from bs4 import BeautifulSoup
from deepdiff import DeepDiff

S3_BUCKET_NAME = os.environ['S3_BUCKET_NAME']
AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']

#log('Uploading cards.json to AWS.')
#s3 = boto3.resource('s3')
#s3.meta.client.upload_file('cards.json', S3_BUCKET_NAME, 'dev/cards.json', ExtraArgs={'ACL': "public-read", 'StorageClass': "REDUCED_REDUNDANCY"})
#time.sleep(5)

def json2csv(file2convert):
    # This section takes the cards.json file as input and outputs a csv file of all card names.
    #
    log(('Converting {} to .csv.').format(file2convert))
    log(('Reading {}.').format(file2convert))
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
    log(('Writing output to {}.').format(file2convertcsv))
    output_card_data.close()

def log(msg):
    print('card_handler # {}'.format(msg))

def differences():
    # This section find the difference between the csv files..
    #

    old = set((line.strip() for line in open('old-cards.csv')))
    new = set((line.strip() for line in open('cards.csv')))

    log('Checking what\'s different and saving to diff.csv.')
    with open('diff.csv', 'w') as diff:
        num_of_differences = 0
        for line in new:
            if line not in old:
                diff.write('{}\n'.format(line))
                num_of_differences += 1

    log(('There were {} new cards detected!').format(num_of_differences))
    return num_of_differences

def readFile(readingFile):
    log(('Reading {}.').format(readingFile))
    card_data = open(readingFile,"r")
    cards_parsed = json.load(card_data)
    return cards_parsed

def findTheIndex(diffs):
    return re.findall(r'(?<=root\[)([0-9]{1,4})',diffs)

def findCardName(cardNumbers):
    count = 0
    interestingRows = list()

    for card in cardNumbers:     
        card = (int(card))
        log(('Card number {}.').format(card))
        with open('cards.csv') as fd:
            reader=csv.reader(fd)
            #log(('count {}').format(count))
            interestingRow = [row for idx, row in enumerate(reader) if idx == card]
            interestingRows.append(interestingRow)
            #log(interestingRows[count])
            count += 1
    log(('There are {} nerfed/buffed cards.').format(count))
    return interestingRows

def saveCardsToCsv(nerfedCards):
    with open('diff.csv', 'w') as diff:
        for x in nerfedCards:
            x = (str(x))
            x = x.strip('[[\'')
            x = x.rstrip('\']]')
            diff.write('{}\n'.format(x))

def downloadCards():
    # This section takes the diff.csv file of card names as input and downloads the card images from legends-decks.com and uploads the images to AWS.
    #

    count = 1

    with open ('diff.csv', newline='') as csvfile:
        cardreader = csv.reader(csvfile, delimiter=',')
        for row in cardreader:
            url = ('http://www.legends-decks.com/img_cards/{}.png'.format(row[0]))
            split = urllib.parse.urlsplit(url)
            filenamePath = "cards/" + split.path.split("/")[-1]
            filename = split.path.split("/")[-1]
            try:
                urllib.request.urlretrieve(url, filename)
            except urllib.error.HTTPError:
                # Do something here to handle the error. For example:
                log(("URL {}{} could not be read.").format(url, filename))
                continue
            log(('Card number {} is {}').format(count,filename))
            log(('Saving file {} locally.').format(filename))
            log(('Uploading {} to AWS.').format(filename))
            s3 = boto3.resource('s3')
            try:
                s3.meta.client.upload_file(filename, S3_BUCKET_NAME, filenamePath, ExtraArgs={'ContentType': "image/png", 'ACL': "public-read", 'StorageClass': "REDUCED_REDUNDANCY"})
            except botocore.exceptions.ClientError as e:
                log(('There was an error uploading {}.').format(filename))
                log(('The error was "{}"').format(e))
            count += 1
    log('Finished uploading cards.')

def uploadToAWS():
    log('Uploading cards.json to AWS.')
    s3 = boto3.resource('s3')
    try:
        s3.meta.client.upload_file('cards.json', S3_BUCKET_NAME, 'cards.json', ExtraArgs={'ACL': "public-read", 'StorageClass': "REDUCED_REDUNDANCY"})
    except botocore.exceptions.ClientError as e:
        log('There was an error uploading cards.json.')
        log(('The error was "{}"').format(e))
    log('Finished.')

if __name__ == '__main__':
    log('Starting..')
    json2csv('cards.json')
    json2csv('old-cards.json')
    log('Finished converting and saving files in csv format.')
    thereAreNewCards = differences()
    if thereAreNewCards > 0:
        downloadCards()
        uploadToAWS()
    else:
        newFile = readFile('cards.json')
        oldFile = readFile('old-cards.json')
        difr = findTheIndex((str(DeepDiff(newFile, oldFile))))
        nerfed = findCardName(difr)
        if len(nerfed)==0:
            log('No nerfed/buffed cards found')
        else:
            saveCardsToCsv(nerfed)
            downloadCards()
            uploadToAWS()
    time.sleep(86400)
