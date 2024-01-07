import datetime
import calendar
import requests
from bs4 import BeautifulSoup
import sys

y = sys.argv[1]
m = sys.argv[2].zfill(2)

if __name__ == "__main__":
    
    # Make a list of the days of the year that are in this month
    num_days = calendar.monthrange(int(y), int(m))[1]
    days = [datetime.date(int(y), int(m), d).timetuple().tm_yday
            for d in range(1, num_days+1)]

    # Form links for all of the files for wget to download this month
    links = []
    for d in days:
        d = str(d).zfill(3)
        base = (f"https://tropomi.gesdisc.eosdis.nasa.gov/data/"
                f"S5P_TROPOMI_Level2/S5P_L2__CH4____HiR.2/{y}/{d}/")
        reqs = requests.get(base)
        soup = BeautifulSoup(reqs.text, 'html.parser')
        for link in soup.find_all('a'):
            link = base+link.get('href')
            processor = ("_020400_" in link) or ("_020500_" in link) or ("_020600_" in link)
            if link[-3:] == ".nc" and link not in links and processor:
                links.append(link)

    # Write the links to links.txt
    with open('links.txt', 'w') as f:
        for link in links:
            f.write(f"{link}\n")