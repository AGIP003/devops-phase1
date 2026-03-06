import requests
from bs4 import BeautifulSoup
import pandas as pd

def scrape_currency():
    # 1. THE TARGET: A simple exchange rate site
    url = "https://www.x-rates.com/table/?from=USD&amount=1"
    
    # 2. THE REQUEST: Getting the HTML
    headers = {'User-Agent': 'Mozilla/5.0'} # Pretending to be a human browser
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        # 3. THE PARSE: Turning HTML into a searchable object
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 4. THE EXTRACTION: Finding the table
        # We look for the 'ratesTable' class in the HTML
        table = soup.find('table', class_='ratesTable')
        rows = table.find_all('tr')
        
        currency_data = []
        
        for row in rows[1:11]: # Just get the top 10 currencies
            cols = row.find_all('td')
            name = cols[0].text
            rate = cols[1].text
            currency_data.append({'Currency': name, 'Rate': rate})
            
        # 5. THE RESULT: Back into our favorite tool, Pandas
        df = pd.DataFrame(currency_data)
        print("--- Live USD Exchange Rates ---")
        print(df)
        return df
    else:
        print(f"Failed to reach site. Error: {response.status_code}")

if __name__ == "__main__":
    scrape_currency()