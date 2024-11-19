import csv
import requests
from bs4 import BeautifulSoup
import logging
from urllib.parse import quote
import os

# logging;
logging.basicConfig(filename='scraper.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def read_companies(file_path):
    with open(file_path, 'r') as f:
        reader = csv.DictReader(f)
        return [row['Longname'] for row in reader]


def generate_url(company_name):
    """generates the URL for a given company; call this if you've changed URL formatting below;"""
    formatted_name = company_name.upper().replace(' ', '-').replace('.COM', '-com').replace('.', '').replace(',', '').replace('&', 'and').replace('"', '').replace('CORPORATION', 'CORP').replace('COMPANY', 'CO').replace('INCORPORATED', 'INC').replace('INDUSTRIES', 'IND')
    encoded_name = quote(formatted_name)
    return f"https://www1.salary.com/{encoded_name}-Executive-Salaries.html"


def generate_member_url(first_name, last_name, company_name, year):
    """generates the URL for a board member's historical data"""
    formatted_name = f"{first_name}-{last_name}".lower().replace('.', '').replace(' ', '-')
    formatted_company = company_name.upper().replace(' ', '-').replace('.COM', '-com').replace('.', '').replace(',', '').replace('&', 'and').replace('"', '').replace('CORPORATION', 'CORP').replace('COMPANY', 'CO').replace('INCORPORATED', 'INC').replace('INDUSTRIES', 'IND')
    encoded_company = quote(formatted_company)
    return f"https://www.salary.com/tools/executive-compensation-calculator/{formatted_name}-board-member-of-{encoded_company}?year={year}"


def generate_and_save_urls(input_file, output_file):
    """generates URLs for all companies and saves them to CSV file; call this if you've changed URL formatting in generate_url();"""
    companies = read_companies(input_file)
    urls = [(company, generate_url(company)) for company in companies]
    
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Company', 'URL'])
        writer.writerows(urls)
    
    logging.info(f"Generated and saved URLs for {len(urls)} companies to {output_file}")
    print(f"Generated and saved URLs for {len(urls)} companies to {output_file}")


def fetch_page(url):
    """fetches the HTML for a generated URL; logs a WARNING if the URL is wrong;"""
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        logging.error(f"Error fetching {url}: {e}")
        print(f"Error fetching {url}: {e}")
        return None


def parse_board_members(html, company_name):
    """parses the HTML and mines board member information;"""
    soup = BeautifulSoup(html, 'html.parser')
    board_members = []
    
    board_section = soup.find('span', string=lambda text: text and 'Board of Directors in' in text)
    if board_section:
        table = board_section.find_next('table', class_='table-executive')
        if table:
            rows = table.find_all('tr')[1:]  # skip header row
            for row in rows:
                columns = row.find_all('td')
                if len(columns) == 2:
                    name = columns[0].find('a').text.strip()
                    compensation = columns[1].text.strip().replace('Total Cash', '').strip()
                    board_members.append({
                        'Company': company_name,
                        'Name': name,
                        'Total Compensation': compensation
                    })
    
    return board_members


def create_folder_if_not_exists(folder_path):
    os.makedirs(folder_path, exist_ok=True)
    print(f"Folder created or already exists: {folder_path}")


def parse_historical_board_members(html):
    """parses the HTML and extracts historical board member information"""
    soup = BeautifulSoup(html, 'html.parser')
    board_members = []
    
    # Find the main container div
    main_div = soup.find('div', class_='sa-layout-section border-top-none padding0 padding-top15 margin-top20 padding-bottom10')
    
    if main_div:
        # Find the flex-div containing the board member links
        flex_div = main_div.find('div', class_='flex-div')
        
        if flex_div:
            # Find all anchor tags with the specified class
            links = flex_div.find_all('a', class_='other-boarddirectors-a')
            
            for link in links:
                name = link.text.strip()
                board_members.append(name)
    
    return board_members


def main():
    input_folder = "input_data"
    input_file = os.path.join(input_folder, "companies.csv")
    output_folder = "output_data"
    url_output = os.path.join(output_folder, "company_urls.csv")
    bm_output = os.path.join(output_folder, "sp500_board_members.csv")

    create_folder_if_not_exists(output_folder)
    
    # generate and save URLs
    generate_and_save_urls(input_file, url_output)
    
    # read URLs from the generated CSV file
    with open(url_output, 'r') as f:
        reader = csv.DictReader(f)
        company_urls = list(reader)
    
    total_companies = len(company_urls)
    total_board_members = 0
    
    # create the output file for current year
    with open(bm_output, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['Company', 'Name', 'Total Compensation'])
        writer.writeheader()
    
    for i, row in enumerate(company_urls, 1):
        company = row['Company']
        url = row['URL']
        print(f"Scraping {company} ({i}/{total_companies})")
        logging.info(f"Scraping {company} ({i}/{total_companies})")
        
        html = fetch_page(url)
        if html:
            board_members = parse_board_members(html, company)
            total_board_members += len(board_members)
            
            # append results to the CSV file for current year
            with open(bm_output, 'a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['Company', 'Name', 'Total Compensation'])
                writer.writerows(board_members)
            
            print(f"Found {len(board_members)} board members for {company}")
            logging.info(f"Found {len(board_members)} board members for {company}")
            
            # scrape historical data
            company_folder = os.path.join(output_folder, company.replace(' ', '_'))
            create_folder_if_not_exists(company_folder)
            
            for year in range(2024, 2018, -1):  # this seems to be a good range
                historical_members = set()
                for member in board_members:
                    first_name, last_name = member['Name'].split(' ', 1)
                    member_url = generate_member_url(first_name, last_name, company, year)
                    
                    logging.info(f"Fetching URL for {first_name} {last_name}, {company}, {year}: {member_url}")
                    
                    member_html = fetch_page(member_url)
                    
                    if member_html:
                        new_members = parse_historical_board_members(member_html)
                        historical_members.update(new_members)
                        logging.info(f"Found {len(new_members)} historical board members for {first_name} {last_name}, {company}, {year}")
                    else:
                        logging.warning(f"No data found for {first_name} {last_name}, {company}, {year}")
                    
                
                # save historical data
                historical_output = os.path.join(company_folder, f"{company}_board_members_{year}.csv")
                with open(historical_output, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Name'])
                    writer.writerows([[name] for name in historical_members])
                
                print(f"Scraped {len(historical_members)} board members for {company} in {year}")
                logging.info(f"Scraped {len(historical_members)} board members for {company} in {year}")

    
    print(f"Scraping completed. Total board members found: {total_board_members}")
    print(f"Results saved to {bm_output} and individual company folders")
    logging.info(f"Scraping completed. Total board members found: {total_board_members}")
    logging.info(f"Results saved to {bm_output} and individual company folders")


if __name__ == "__main__":
    main()