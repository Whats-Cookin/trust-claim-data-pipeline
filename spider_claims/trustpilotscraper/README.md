# How to run Truspilot bot
## Clone the repo or branch
- go to your terminal and type 'git clone --branch --single-branch https://github.com/Whats-Cookin/Sandbox-test-scraping.git'
## Download all required packages
- In your terminal go into truspilot -> 'cd truspilot'
- Type 'pip install -r requirements.txt'
Creating a virtual environment is encouraged before the above process
## Run it
- Check if you can see the .env file. if it in place, then you are good to go
- Go into the trustpilotscraper -> 'cd trustpilotscraper'
- In your terminal run using 'scrapy crawl trustpilotspider'
- Check for trustpilotdata.json and trustpilotdata.csv 
