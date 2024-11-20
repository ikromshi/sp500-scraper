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
