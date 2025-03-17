import os
import requests
from bs4 import BeautifulSoup
import csv
# Function to accept the disclaimer
def accept_disclaimer(session):
    disclaimer_url = "https://www.thecountyrecorder.com/Disclaimer.aspx?RU=%2FIntroduction.aspx"
    
    # Send GET request to the Disclaimer page
    response = session.get(disclaimer_url)
    
    if response.status_code == 200:
        print("Disclaimer page loaded successfully.")
        
        # Parse the disclaimer page to ensure it's loaded correctly
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the 'Yes, I Accept' button
        accept_button = soup.find("input", {"id": "MainContent_searchMainContent_ctl01_btnAccept"})
        if accept_button:
            # Get the form action URL (usually the current page URL or a relative path)
            form_action = soup.find("form")["action"]
            
            # Submit the form to accept the disclaimer
            form_data = {
                "ctl00$ctl00$MainContent$searchMainContent$ctl01$btnAccept": "Yes, I Accept"
            }
            
            # Send POST request to accept the disclaimer and proceed
            post_response = session.post(f"https://www.thecountyrecorder.com{form_action}", data=form_data)
            
            if post_response.status_code == 200:
                print("Successfully accepted the disclaimer.")
                return True
            else:
                print(f"Failed to accept the disclaimer. Status code: {post_response.status_code}")
                return False
        else:
            print("Could not find the 'Yes, I Accept' button.")
            return False
    else:
        print(f"Failed to load disclaimer page. Status code: {response.status_code}")
        return False

# Function to set up the search form on Search.aspx
def setup_search(session, state, county, start_date, end_date):
    search_url = "https://www.thecountyrecorder.com/Search.aspx"
    
    # Prepare the form data
    form_data = {
        'ctl00$ctl00$MainContent$searchMainContent$ctl01$ctl00$cboStates': state,
        'ctl00$ctl00$MainContent$searchMainContent$ctl01$ctl00$cboCounties': county,
        'ctl00$ctl00$MainContent$searchMainContent$ctl00$tbDateStart': start_date,
        'ctl00$ctl00$MainContent$searchMainContent$ctl00$tbDateEnd': end_date,
        'ctl00$ctl00$MainContent$searchMainContent$ctl01$ctl00$DocumentGroup': 'Lien',
        'ctl00$ctl00$MainContent$searchMainContent$ctl01$ctl00$btnSearch': 'Search'
    }
    
    # Perform POST request to submit the search form
    response = session.post(search_url, data=form_data)
    
    if response.status_code == 200:
        print("Search form submitted successfully.")
        return response.text
    else:
        print(f"Failed to submit search form. Status code: {response.status_code}")
        return None

# Function to parse the results and download files
def get_results_and_download(soup, output_folder, start_date, end_date):
    print("Parsing search results...")

    # Ensure the output folder exists
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Find all rows in the results table (assuming results are in a <table> tag)
    table = soup.find("table", class_="results-table")  # Adjust based on the actual HTML structure
    rows = table.find_all("tr")[1:]  # Skip the header row (if exists)

    # Prepare the CSV file to save results
    with open(f"{output_folder}/search_results.csv", mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Document ID", "Title", "Date", "Lien Type", "URL"])

        # Loop through each row and extract details
        for row in rows:
            # Extract date from the 'td' with class "results-data-cell"
            date_cell = row.find("td", class_="results-data-cell")
            if date_cell:
                date = date_cell.text.strip()

                # Check if the date falls within the specified date range
                if start_date <= date <= end_date:
                    doc_id = row.find("td", class_="doc_id").text.strip() if row.find("td", class_="doc_id") else "N/A"
                    title = row.find("td", class_="title").text.strip() if row.find("td", class_="title") else "N/A"
                    lien_type = row.find("td", class_="lien_type").text.strip() if row.find("td", class_="lien_type") else "N/A"
                    doc_url = row.find("a", class_="doc_url")["href"] if row.find("a", class_="doc_url") else None

                    # Write the row to the CSV
                    writer.writerow([doc_id, title, date, lien_type, doc_url])

                    # Download associated files (images, PDFs, etc.)
                    if doc_url:
                        download_files(doc_url, output_folder)
# Function to download files (PDFs, images, etc.)
def download_files(doc_url, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    file_url = f"https://www.thecountyrecorder.com{doc_url}"

    response = requests.get(file_url)
    if response.status_code == 200:
        file_name = os.path.join(output_folder, doc_url.split("/")[-1])
        with open(file_name, 'wb') as file:
            file.write(response.content)
        print(f"Downloaded {file_name}")
    else:
        print(f"Failed to download {file_url}")

# Main scraping function
def scrape(state, county, start_date, end_date, output_folder):
    session = requests.Session()
    
    # Step 1: Accept the disclaimer
    if not accept_disclaimer(session):
        return
    
    # Step 2: Set up the search form and get the search results
    search_page_html = setup_search(session, state, county, start_date, end_date)
    
    if search_page_html:
        soup = BeautifulSoup(search_page_html, 'html.parser')

        # Step 3: Parse results and download files
        get_results_and_download(soup, output_folder)

# Ask user for input
def user_input():
    state = "COLORADO"
    county = "Teller"
    start_date = "01-01-2020"
    end_date = "12-31-2020"
    output_folder = "output"

    # state = input("Enter the state (e.g., ARIZONA, COLORADO): ")
    # county = input("Enter the county: ")
    # start_date = input("Enter the start date (MM/DD/YYYY): ")
    # end_date = input("Enter the end date (MM/DD/YYYY): ")
    # output_folder = input("Enter the folder name for saving results: ")

    return state, county, start_date, end_date, output_folder

# Main entry point
if __name__ == "__main__":
    state, county, start_date, end_date, output_folder = user_input()
    scrape(state, county, start_date, end_date, output_folder)


# Debug with Colorado and Teller County
state = "COLORADO"
county = "Teller"
start_date = "01-01-2020"
end_date = "12-31-2020"
output_folder = "output"

# Call scrape function
scrape(state, county, start_date, end_date, output_folder)
