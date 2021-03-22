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

min_cena = 14000
min_ocena = 1000

timeout = 10 ## sekunde
br_oglasa = 3 ## po stranici
br_stranica = 20

greska_za_redom = 0
ispunjeni = 0

procesori_ws = sh.get_worksheet(0)
procesori_ws.clear()

procesori_ws.update_cell(1, 1, "Link ka KP oglasu")
procesori_ws.update_cell(1, 2, f"Cena (>= {min_cena})")
procesori_ws.update_cell(1, 3, f"Ocena korisnika (>= {min_ocena})")

kpURL = "https://www.kupujemprodajem.com"

for k in range(1, br_stranica+1):

    if greska_za_redom < 3:

        print("------------KP stranica " + str(k) + "/" + str(br_stranica) + "------------")

        CPU_SEARCH_URL = "https://www.kupujemprodajem.com/kompjuteri-desktop/procesori/search.php?action=list&data%5B_page_url%5D=kompjuteri-desktop%2Fprocesori%2Fsearch.php&data%5Baction%5D=list&data%5Bsubmit%5D%5Bsearch%5D=Traži&data%5Bdummy%5D=name&data%5Bpage%5D=" + str(k) + "&data%5Bad_kind%5D=goods&data%5Bcategory_id%5D=10&data%5Bgroup_id%5D=94&data%5Border%5D=price&data%5Bprice_from%5D=" + str(min_cena) + "&data%5Bcurrency%5D=rsd&data%5Bhas_price%5D=yes&data%5Blist_type%5D=search"

        page = requests.get(CPU_SEARCH_URL)
    
        soup = BeautifulSoup(page.content, 'html.parser', from_encoding="iso-8859-1")

        ceneHTML = soup.find_all('span', "adPrice")
        adsHTML = soup.find_all('a', "adName")

        br_oglasa = len(ceneHTML)

        for i in trange(0, br_oglasa): ## parsing cena, pa lajkova
        
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


            if re.search("i5", name, re.IGNORECASE) or re.search("i7", name, re.IGNORECASE) or re.search("ryzen 5 3", name, re.IGNORECASE) or re.search("ryzen 5 5", name, re.IGNORECASE) or re.search("ryzen 7", name, re.IGNORECASE): ## glavni uslov, posle tek lajkovi
                ## odavde parsing lajkova
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

                    print(f"{name}, indeks: {i}, {likeCount} lajkova")
                    print("Oglas ispunjava kriterijum, upis u google sheets...\n")

                    procesori_ws.update_cell(ispunjeni+1, 1, link_str)
                    procesori_ws.update_cell(ispunjeni+1, 2, cena)
                    procesori_ws.update_cell(ispunjeni+1, 3, likeCount)

                    time.sleep(timeout)

                    #procesori_ws.sort((3, "des"), range="A2:C91") ## sort po oceni, opadajuce


            else:
                print(name  + ", indeks: " + str(i))
                print("Ne ispunjava glavni uslov\n")

        if k<br_stranica+1:
            print(f"Pauza {timeout*5} sekundi nakon otvaranja stranice\n")
            time.sleep(timeout*5)

    else:
        print("KP je verovatno blokirao IP, vise od 3 greske za redom, break...\n")
        break

print("kraj skripte")
            
#with open('kp_procesori.csv', 'w') as procesori_file:
#    procesori_writer = csv.writer(procesori_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
#    procesori_writer.writerow(["Link KP stranice", "Oglas", "Cena", "Ocena korisnika"])
#    for i in trange(0, len(links)):
#        procesori_writer.writerow([links[i], names[i], cene[i], likes[i]]) ##print(" Upisan red " + str(i+1) + "/" + str(len(links)) + "...")