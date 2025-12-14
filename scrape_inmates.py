from inmate_lookup import InmateLookup

if __name__ == "__main__":
    lookup = InmateLookup()
    lookup.open_home_page()
    result = lookup.do_inmate_search()
    print(result)
