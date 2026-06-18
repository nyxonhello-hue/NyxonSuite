import requests
from bs4 import BeautifulSoup
import csv

base_url = "http://quotes.toscrape.com/page/"

for page in range(1,6):
    url = base_url.format(page)
    reponse = requests.get(url)

    soup = BeautifulSoup(reponse.text, "html.bparser")

    quotes = soup.find_all("div",class_="quote")

    for q in quotes:
        text = q.find("span",class_="text").text
        author = q.find("small", class_ ="author").text
        print(text,"-" ,author)