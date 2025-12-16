from bs4 import BeautifulSoup
from inmate_lookup import InmateLookup
import json

def parse_inmates(html_file):
    with open(html_file, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')
    
    inmates = []
    # Find all rows that have an id starting with "row"
    rows = soup.find_all('tr', id=lambda x: x and x.startswith('row'))
    
    for row in rows:
        cells = row.find_all('td')
        if len(cells) >= 5:
            inmate = {
                'name': cells[0].get_text(strip=True),
                'booking_number': cells[1].get_text(strip=True),
                'permanent_id': cells[2].get_text(strip=True),
                'date_of_birth': cells[3].get_text(strip=True),
                'release_date': cells[4].get_text(strip=True)
            }
            inmates.append(inmate)
            
    return inmates

if __name__ == "__main__":
    lookup = InmateLookup()
    lookup.open_home_page()
    result = lookup.do_inmate_search()
    
    with open("results.html", "w", encoding="utf-8") as f:
        f.write(str(result))
        
    inmates = parse_inmates("results.html")
    print(json.dumps(inmates, indent=4))
