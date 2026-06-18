import requests
from bs4 import BeautifulSoup
import csv

url = "http://quotes.toscrape.com"
reponse = requests.get(url)

soup = BeautifulSoup(reponse.text,"html.parser")

quotes = soup.find_all("div",class_="quote")

for q in quotes:
    text = q.find("span",class_="text").text
    author = q.find("small",class_="author").text
    print(text, "_", author)



with open("quotes.csv",'w', newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["quote", "Author"])

    for q in quotes:
        text = q.find("span", class_="text").text
        author = q.find("small", class_="author").text

        writer.writerow([text, author])