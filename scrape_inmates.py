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
    inmates = []
    last_inmates = []
    current_start = 0

    lookup = InmateLookup()
    lookup.open_home_page()

    while True:
        raw_html = ''
        if current_start == 0:
            raw_html = lookup.do_inmate_search()
        else:
            raw_html = lookup.do_inmate_search_next(current_start)
        
        with open("results.html", "w", encoding="utf-8") as f:
            f.write(str(raw_html))
        last_inmates = parse_inmates("results.html")
        inmates.extend(last_inmates)
        
        if len(last_inmates) == 0:
            break
        
        current_start = len(inmates) + 1
        print("Inmate Count: " + str(len(inmates)))

    print(json.dumps(inmates, indent=4))
    print("Total inmates: " + str(len(inmates)))
