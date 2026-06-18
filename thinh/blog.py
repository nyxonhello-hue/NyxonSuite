import requests
from bs4 import BeautifulSoup
import csv

url = "https://blog.python.org/"
reponse = requests.get(url)

soup = BeautifulSoup(reponse.text, "html.parser")

posts = soup.find_all("h3", class_="post-title entry-title")

for post in posts:
    title = post.text.strip()
    link = post.find("a")["href"]

    print(link)
    print(title)
    print("-" * 40)

with open("blog_posts.csv","w",newline="", encoding="utf-8") as file: 
    writer = csv.writer(file)
    writer.writerow(["Title", "Link"])  

    for post in posts:
        title = post.text.strip()
        link = post.find("a")["href"]
        writer.writerow([title, link]) 
