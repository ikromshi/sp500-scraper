import csv
import requests
from bs4 import BeautifulSoup
import logging
from urllib.parse import quote
import os
import uuid

# Set up logging
logging.basicConfig(filename='scraper.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def read_companies(file_path):
    with open(file_path, 'r') as f:
        reader = csv.DictReader(f)
        return [row['Longname'] for row in reader]

def generate_url(company_name):
    formatted_name = company_name.upper().replace(' ', '-').replace('.COM', '-com').replace('.', '').replace(',', '').replace('&', 'and').replace('"', '').replace('CORPORATION', 'CORP').replace('COMPANY', 'CO').replace('INCORPORATED', 'INC').replace('INDUSTRIES', 'IND')
    encoded_name = quote(formatted_name)
    return f"https://www1.salary.com/{encoded_name}-Executive-Salaries.html"

def generate_member_url(first_name, last_name, company_name, year):
    formatted_name = f"{first_name}-{last_name}".lower().replace('.', '').replace(' ', '-')
    formatted_company = company_name.upper().replace(' ', '-').replace('.COM', '-com').replace('.', '').replace(',', '').replace('&', 'and').replace('"', '').replace('CORPORATION', 'CORP').replace('COMPANY', 'CO').replace('INCORPORATED', 'INC').replace('INDUSTRIES', 'IND')
    encoded_company = quote(formatted_company)
    return f"https://www.salary.com/tools/executive-compensation-calculator/{formatted_name}-board-member-of-{encoded_company}?year={year}"

def fetch_page(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        logging.error(f"Error fetching {url}: {e}")
        print(f"Error fetching {url}: {e}")
        return None

def parse_board_members(html, company_name):
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
                        'Name': name,
                        'Total Compensation': compensation
                    })
    
    return board_members

def parse_historical_board_members(html):
    soup = BeautifulSoup(html, 'html.parser')
    board_members = []
    
    main_div = soup.find('div', class_='sa-layout-section border-top-none padding0 padding-top15 margin-top20 padding-bottom10')
    
    if main_div:
        flex_div = main_div.find('div', class_='flex-div')
        
        if flex_div:
            links = flex_div.find_all('a', class_='other-boarddirectors-a')
            
            for link in links:
                name = link.text.strip()
                board_members.append(name)
    
    return board_members

def parse_compensation_data(html):
    soup = BeautifulSoup(html, 'html.parser')
    compensation_data = {}
    
    compensation_div = soup.find('div', class_='sa-layout-section border-top-none padding0 bluegreengradient')
    if compensation_div:
        name_div = compensation_div.find('h3', class_='sa-cat-links-title text-size22 padding-left25 padding-top25')
        if name_div:
            name = name_div.text.strip()
            compensation_data['Name'] = name

        total_compensation = compensation_div.find('div', class_='font-semibold text-size18 text-blue')
        if total_compensation:
            compensation_data['Total Compensation'] = total_compensation.text.strip()
    
    return compensation_data

def create_csv_writers(output_folder):
    os.makedirs(output_folder, exist_ok=True)
    
    companies_file = open(os.path.join(output_folder, 'companies.csv'), 'w', newline='')
    companies_writer = csv.DictWriter(companies_file, fieldnames=['id', 'name'])
    companies_writer.writeheader()
    
    board_members_file = open(os.path.join(output_folder, 'board_members.csv'), 'w', newline='')
    board_members_writer = csv.DictWriter(board_members_file, fieldnames=['id', 'name'])
    board_members_writer.writeheader()
    
    mappings_file = open(os.path.join(output_folder, 'mappings.csv'), 'w', newline='')
    mappings_writer = csv.DictWriter(mappings_file, fieldnames=['id', 'company_id', 'board_member_id', 'year', 'total_compensation'])
    mappings_writer.writeheader()
    
    return {
        'companies': (companies_file, companies_writer),
        'board_members': (board_members_file, board_members_writer),
        'mappings': (mappings_file, mappings_writer)
    }

def main():
    input_folder = "input_data"
    input_file = os.path.join(input_folder, "companies.csv")
    output_folder = "output_data"
    
    companies = read_companies(input_file)
    csv_writers = create_csv_writers(output_folder)
    
    company_ids = {}
    board_member_ids = {}
    
    for company in companies:
        company_id = str(uuid.uuid4())
        company_ids[company] = company_id
        csv_writers['companies'][1].writerow({'id': company_id, 'name': company})
        
        url = generate_url(company)
        print(f"Scraping {company}")
        logging.info(f"Scraping {company}")
        
        html = fetch_page(url)
        if html:
            board_members = parse_board_members(html, company)
            
            for year in range(2024, 2018, -1):
                for member in board_members:
                    first_name, last_name = member['Name'].split(' ', 1)
                    member_url = generate_member_url(first_name, last_name, company, year)
                    
                    logging.info(f"Fetching URL for {first_name} {last_name}, {company}, {year}: {member_url}")
                    
                    member_html = fetch_page(member_url)
                    
                    if member_html:
                        new_members = parse_historical_board_members(member_html)
                        compensation_data = parse_compensation_data(member_html)
                        
                        # Process current member
                        if member['Name'] not in board_member_ids:
                            board_member_id = str(uuid.uuid4())
                            board_member_ids[member['Name']] = board_member_id
                            csv_writers['board_members'][1].writerow({'id': board_member_id, 'name': member['Name']})
                        
                        mapping_id = str(uuid.uuid4())
                        csv_writers['mappings'][1].writerow({
                            'id': mapping_id,
                            'company_id': company_ids[company],
                            'board_member_id': board_member_ids[member['Name']],
                            'year': year,
                            'total_compensation': compensation_data.get('Total Compensation', 'N/A')
                        })
                        
                        # Process other board members
                        for new_member in new_members:
                            if new_member not in board_member_ids:
                                board_member_id = str(uuid.uuid4())
                                board_member_ids[new_member] = board_member_id
                                csv_writers['board_members'][1].writerow({'id': board_member_id, 'name': new_member})
                            
                            mapping_id = str(uuid.uuid4())
                            csv_writers['mappings'][1].writerow({
                                'id': mapping_id,
                                'company_id': company_ids[company],
                                'board_member_id': board_member_ids[new_member],
                                'year': year,
                                'total_compensation': 'N/A'
                            })
                        
                        logging.info(f"Processed {len(new_members)} board members for {company} in {year}")
                    else:
                        logging.warning(f"No data found for {first_name} {last_name}, {company}, {year}")
                    
    
    # Close all CSV files
    for file, _ in csv_writers.values():
        file.close()
    
    print(f"Scraping completed. Results saved to {output_folder}")
    logging.info(f"Scraping completed. Results saved to {output_folder}")

if __name__ == "__main__":
    main()