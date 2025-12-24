from bs4 import BeautifulSoup
from inmate_lookup import InmateLookup
import json
import csv
import os
import argparse

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
            
            onclick = row.get('onclick')
            if onclick:
                # onclick format: rowClicked('1','21860256738722','21860256738722')
                # We want the second argument
                parts = onclick.split("'")
                if len(parts) >= 4:
                    inmate['system_id'] = parts[3]
                    
            inmates.append(inmate)
            
    return inmates

def parse_inmate_details(html_file):
    with open(html_file, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')
        
    data = {}

    # Extract Name
    name_div = soup.find('div', class_='header')
    if name_div:
        full_text = name_div.get_text(strip=True)
        if full_text.startswith("Name:"):
            data['name'] = full_text[5:].strip()

    # Extract Key-Value Pairs (Personal Info, Inmate Info, Incarceration Info)
    key_value_pairs = {}
    bold_tds = soup.find_all('td', class_='bodysmallbold')
    for td in bold_tds:
        key = td.get_text(strip=True).rstrip(':')
        # Value is usually next sibling td
        next_td = td.find_next_sibling('td')
        if next_td:
            value = next_td.get_text(strip=True)
            # avoid empty keys
            if key:
                 key_value_pairs[key] = value
    
    data['details'] = key_value_pairs
    
    # Parse List-based Tables (Charges, Bonds)
    all_tables = soup.find_all('table')
    
    # Charges
    charges = []
    for table in all_tables:
        # Look for a table that has "Case #" and "Offense Date" in a header row
        # This avoids the "Charge Information" nested table issue
        header_row = table.find('tr', class_='bodysmallbold')
        if header_row:
             header_text = header_row.get_text(strip=True)
             if "Case #" in header_text and "Offense Date" in header_text and "Code" in header_text:
                rows = table.find_all('tr')
                for row in rows:
                    # Skip the header row itself
                    if row == header_row:
                        continue
                        
                    cells = row.find_all('td')
                    # Expecting at least 6 cells
                    if len(cells) >= 6:
                        # Ensure it's a data row (usually class 'bodysmall')
                        # Check first cell content or just try to get text
                        charge = {
                             'case_number': cells[0].get_text(strip=True),
                             'offense_date': cells[1].get_text(strip=True),
                             'code': cells[2].get_text(strip=True),
                             'description': cells[3].get_text(strip=True),
                             'grade': cells[4].get_text(strip=True),
                             'degree': cells[5].get_text(strip=True),
                        }
                        # Basic validity check (case number or date should exist)
                        if charge['offense_date'] or charge['code']:
                             charges.append(charge)
                # Once found, break (assuming only one charge table per page)
                data['charges'] = charges
                break

    # Bonds
    bonds = []
    for table in all_tables:
        header_row = table.find('tr', class_='bodysmallbold')
        if header_row:
             header_text = header_row.get_text(strip=True)
             if "Bond Type" in header_text and "Amount" in header_text:
                  rows = table.find_all('tr')
                  for row in rows:
                      if row == header_row:
                          continue
                      
                      cells = row.find_all('td')
                      if len(cells) >= 9:
                          bond = {
                              'case_number': cells[0].get_text(strip=True),
                              'bond_type': cells[1].get_text(strip=True),
                              'amount': cells[2].get_text(strip=True),
                              'status': cells[3].get_text(strip=True),
                              'percent': cells[4].get_text(strip=True),
                              'set_by': cells[5].get_text(strip=True),
                              'additional': cells[6].get_text(strip=True),
                              'set_date': cells[7].get_text(strip=True),
                              'total': cells[8].get_text(strip=True),
                          }
                          if bond['bond_type']:
                              bonds.append(bond)
                  data['bonds'] = bonds
                  break
                  
    # Detainer Information
    # Search for a table with "Comp Number" in the header
    data['detainers'] = []
    
    for table in all_tables:
        header_row = table.find('tr', class_='bodysmallbold')
        if header_row:
            header_text = header_row.get_text(strip=True)
            if "Comp No" in header_text:
                # Found the detainer table
                headers = header_row.find_all('td')
                
                # Map required columns to their indices
                col_indices = {}
                for i, h in enumerate(headers):
                    text = h.get_text(strip=True)
                    if "Comp No" in text:
                        col_indices["Comp No"] = i
                    elif "Comp Date" in text:
                        col_indices["Comp Date"] = i
                    elif "Issued By" in text:
                        col_indices["Issued By"] = i
                    elif "Set By" in text:
                        col_indices["Set By"] = i
                    elif "Total" in text:
                        col_indices["Total"] = i

                rows = table.find_all('tr')
                
                for row in rows:
                    if row == header_row:
                        continue
                    
                    # Skip rows that appear to be headers or footers
                    row_text = row.get_text(strip=True)
                    if "Grand Total" in row_text or "Detainer Information" in row_text:
                        continue

                    cells = row.find_all('td')
                    
                    # We need to ensure the row has enough cells to cover our columns
                    # At least cover the Comp No column
                    if "Comp No" in col_indices and len(cells) > col_indices["Comp No"]:
                        detainer = {}
                        # Extract data for each column found
                        for key, index in col_indices.items():
                            if len(cells) > index:
                                detainer[key] = cells[index].get_text(strip=True)
                            else:
                                detainer[key] = ""
                        
                        # Only add if we have a valid Comp No
                        if detainer.get("Comp No"):
                            data['detainers'].append(detainer)
                break

    return data

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Inmate Scraper')
    parser.add_argument('--scrape', action='store_true', help='Run the scraper')
    parser.add_argument('--csv', action='store_true', help='Turn the json into csv')
    args = parser.parse_args()

    # Nothing happens unless flags are provided
    if not args.scrape and not args.csv:
        exit()

    inmates = []

    if args.scrape:
        # delete inmates.json
        if os.path.exists("inmates.json"):
            os.remove("inmates.json")
        
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
            
            with open("inmate_search.html", "w", encoding="utf-8") as f:
                f.write(str(raw_html))
            last_inmates = parse_inmates("inmate_search.html")
            inmates.extend(last_inmates)
            
            if len(last_inmates) == 0:
                break
                
            current_start = len(inmates) + 1
            print("Inmate Count: " + str(len(inmates)))

        cur_inmate_count = 0
        for inmate in inmates:
            cur_inmate_count += 1
            print("Getting inmate details " + str(cur_inmate_count) + " of " + str(len(inmates)))
            raw_html = lookup.get_inmate_details(inmate['system_id'])
            with open("inmate_details.html", "w", encoding="utf-8") as f:
                f.write(str(raw_html))
            
            details = parse_inmate_details("inmate_details.html")
            inmate.update(details)
        
        with open("inmates.json", "w", encoding="utf-8") as f:
            json.dump(inmates, f, indent=4)
    
    if args.csv:
        # If we didn't scrape in this run, try to load from existing file
        if not args.scrape:
            if os.path.exists("inmates.json"):
                with open("inmates.json", "r", encoding="utf-8") as f:
                    inmates = json.load(f)
            else:
                print("inmates.json not found. Please run with --scrape first to generate data.")
                exit()
        
        # delete inmates.csv if it exists
        if os.path.exists("inmates.csv"):
            os.remove("inmates.csv")

        # Generate CSV
        # Columns: Name, ICE#, Commitment Date, Citizen, Country of Birth, Charge Code, Detainer Comp Number
        print("Generating CSV...")
        with open("inmates.csv", "w", newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Name', 'Booking Number', 'ICE#', 'Commitment Date', 'Citizen', 'Country of Birth', 'Charge Code', 'Detainer Comp Number']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for inmate in inmates:
                details = inmate.get('details', {})
                charges = inmate.get('charges', [])
                
                # Aggregate Charge Codes
                charge_codes = "; ".join([c.get('code', '') for c in charges if c.get('code')])
                
                # Detainer Comp Number
                detainer_list = inmate.get('detainers', [])
                comp_numbers = []
                for d in detainer_list:
                    if isinstance(d, dict):
                        comp_numbers.append(d.get('Comp No', ''))
                    else:
                        comp_numbers.append(str(d))
                detainer_comp_number = "; ".join(comp_numbers) 
                
                writer.writerow({
                    'Name': inmate.get('name', ''),
                    'Booking Number': inmate.get('booking_number', ''),
                    'ICE#': details.get('ICE #', ''),
                    'Commitment Date': details.get('Commitment Date', ''),
                    'Citizen': details.get('Citizen', ''),
                    'Country of Birth': details.get('Country of Birth', ''),
                    'Charge Code': charge_codes,
                    'Detainer Comp Number': detainer_comp_number
                })
        print("CSV Generated: inmates.csv")
