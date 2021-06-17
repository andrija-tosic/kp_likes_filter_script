#!/usr/bin/env python3
# coding: utf8
import requests
from bs4 import BeautifulSoup
import csv

import gspread
from oauth2client.service_account import ServiceAccountCredentials

import time
from tqdm import trange

import re

scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets', "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

credentials = ServiceAccountCredentials.from_json_keyfile_name('kp-skripta.json', scope)
client = gspread.authorize(credentials)

print("Otvara se spreadsheet...")
sh = client.open('kp_skripta')

print(client.openall())

min_ocena = 100 

timeout = 3 #10 ## sekunde
br_oglasa = 30 ## po stranici
br_stranica = 50 ## 20

greska_za_redom = 0
ispunjeni = 0

worksheet = sh.get_worksheet(3)
worksheet.clear()

worksheet.update_cell(1, 1, "Link ka KP oglasu")
worksheet.update_cell(1, 2, "Cena")
worksheet.update_cell(1, 3, f"Ocena korisnika (>= {min_ocena})")

kpURL = "https://www.kupujemprodajem.com"

query = input("Search: ")

query = query.lower()
query = query.replace(" ", "+")


for k in range(1, br_stranica+1):

    if greska_za_redom < 3:

        print("------------KP stranica " + str(k) + "/" + str(br_stranica) + "------------")

        SEARCH_URL = "https://www.kupujemprodajem.com/search.php?action=list&data%5Baction%5D=list&data%5Bsubmit%5D%5Bsearch%5D=Tra%C5%BEi&data%5Bdummy%5D=name&data%5Bkeywords%5D=" + query + "&data%5Blist_type%5D=search&data%5Bpage%5D=" + str(k)

        page = requests.get(SEARCH_URL)
    
        soup = BeautifulSoup(page.content, 'html.parser', from_encoding="iso-8859-1")

        ceneHTML = soup.find_all('span', "adPrice")
        adsHTML = soup.find_all('a', "adName")

        br_oglasa = len(ceneHTML)

        for i in range(0, br_oglasa): ## parsing cena, pa lajkova
        
            if ceneHTML[i].text.strip()[-1] == "€":
                cena_str = ceneHTML[i].text.strip().split(',')[0]
                cena = (int(cena_str) * 118) ## eur
            elif ceneHTML[i].text.strip() != "Kupujem":
                cena_str = ceneHTML[i].text.strip().split('\xa0')[0]
                cena = (int(cena_str.replace('.', '').strip())) ## din
            else:
                cena = -1 ## ako pise Kupujem
            link = (adsHTML[i].get("href"))
            name = (adsHTML[i].text.strip())
            
            index = i+1 + br_oglasa*(k-1)
            print(f"[{index}] {name}")

            ## odavde parsing lajkova

            print("Pauza " + str(timeout) + " sekundi...")
            time.sleep(timeout)

            adPage = requests.get(kpURL + str(link))
            soup = BeautifulSoup(adPage.content, 'html.parser', from_encoding="iso-8859-1")
            likeCount = soup.find("div", "thumb-up")

            if (likeCount):
                likeCount = int(likeCount.text.strip())
                greska_za_redom = 0

            else:
                print("Sakriveni lajkovi")
                likeCount = -1
                greska_za_redom += 1


            if likeCount >= min_ocena:
                ispunjeni += 1

                link = kpURL + str(link).strip()

                link_str = f"=HYPERLINK(\"{link}\", \"{name}\")"

                print(f"{name}, indeks: {index}, {likeCount} lajkova")
                print("Oglas ispunjava kriterijum, upis u google sheets...\n")

                worksheet.update_cell(ispunjeni+1, 1, link_str)
                worksheet.update_cell(ispunjeni+1, 2, cena)
                worksheet.update_cell(ispunjeni+1, 3, likeCount)

                worksheet.sort((3, "des"), range="A1:C999") ## sort po oceni, opadajuce
            else:
                print(f"Broj lajka je {likeCount}, manje je od minimum od {min_ocena}")

    else:
        print("KP je verovatno blokirao IP, vise od 3 greske za redom, break...\n")
        break

print("kraj skripte")
            
#with open('kp_procesori.csv', 'w') as procesori_file:
#    procesori_writer = csv.writer(procesori_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
#    procesori_writer.writerow(["Link KP stranice", "Oglas", "Cena", "Ocena korisnika"])
#    for i in trange(0, len(links)):
#        procesori_writer.writerow([links[i], names[i], cene[i], likes[i]]) ##print(" Upisan red " + str(i+1) + "/" + str(len(links)) + "...")
