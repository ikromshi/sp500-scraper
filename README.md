# S&P 500 scraper

This repo scrapes board member information for S&P 500 companies from https://www1.salary.com/.

## Setup

1. Clone the repo:

   ```
   git clone https://github.com/ikromshi/s_and_p_500_board_scraper.git
   cd sp500-scraper
   ```

2. Create and activate a virtual environment:

   ```
   python -m venv venv
   source venv/bin/activate  # on Windows, use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

## Usage

CD into /src and run the scraper:

```
cd src
python scraper.py
```

## Output

`scraper.py` generates two main output files:

1. `company_urls.csv`: contains the generated URLs for all companies.
2. `sp500_board_members.csv`: contains the scraped board member information for all companies.

These files are saved in the `output_data` directory.

## Logging

The scraper continuously its results to `scraper.log`. Every company with a warning has its URL wrong. You can then go into `company_urls` to indvidually change the URLs into the correct format. I've done my best to automate this part, but some URLs aren't intuitive at all and very random.
