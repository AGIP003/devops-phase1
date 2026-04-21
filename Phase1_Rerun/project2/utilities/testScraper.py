import requests
from bs4 import BeautifulSoup


url = "https://news.ycombinator.com/"

#Make Requests : Getting the html
headers = {'User-Agent': 'Mozilla/5.0 (Learning Project)'}

response = requests.get(url, headers=headers)

print(response.status_code)
#print(response.text[:500])

src = response.content

soup = BeautifulSoup(response.text, "html.parser")

#if you want to see thge links in the page
links = soup.find_all("a")

for link in links:
    if "About" in link.text:
        print(link)
        print(link.attrs['href'])
#print(links)
#if response.status_code == 200:


data = soup.find_all("tag")
print(data)
#for item in data:
#    print(item.text)