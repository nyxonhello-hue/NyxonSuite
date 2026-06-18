import requests
from bs4 import BeautifulSoup

url = "https://blog.python.org/"
headers = {"User-Agent":"Mozilla/5.0"}
response = requests.get(url, headers=headers)

soup = BeautifulSoup(response.text, "html.parser")
posts = soup.find_all("article",clas_="post-card")

for post in posts:
    title = post.find("h3").text.strip()
    link = post.find("a")["href"]
    
    full_link = "https://blog.python.org" + link

    print(title)
    print(link)
    print("-" * 40)