import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

url = "https://books.toscrape.com/"
respone = requests.get(url)

soup = BeautifulSoup("respone","html.parser")

images = soup.find_all("img")

for i, img in enumerate(images):
    src = img.get("src")
    full_url = urljoin(url, src)

    img_data = requests.get(full_url).content

    with open(f"image_(i).jpg","wb") as f:
        f.write(img_data)

        print("Download:", full_url)
        