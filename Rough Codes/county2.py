import os
import requests
from bs4 import BeautifulSoup
import csv
from datetime import datetime

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

    # # Find all rows in the results table (assuming results are in a <table> tag)
    # table = soup.find("table", id="MainContent_searchMainContent_ctl00_Table2", class_="Results")
    # print(table)
    # rows = table.find_all("td")[1:]  # Skip the header row (if exists)

   # Find the outer table with id 'tableMain'
   # Find the outer table with id 'tableMain'
    parent_table = soup.find("table", id="tableMain")
    if parent_table:
        # Find the div with id 'PrintResults' directly
        print(parent_table)
        print_results_div = parent_table.find("div", id="PrintResults")
        
        if print_results_div:
            # Now find the results table inside the 'PrintResults' div
            results_table = print_results_div.find("table", id="MainContent_searchMainContent_ctl00_Table2", class_="Results")
            
            if results_table:
                # Find all rows with the appropriate class that hold the data
                rows = results_table.find_all("tr", class_=["results-data-row", "results-data-row listitem-background-color2", "results-data-row listitem-background-color1"])
                
                # Iterate through each row
                for row in rows:
                    cells = row.find_all("td")
                    # Extract data from each row
                    item_number = cells[0].text.strip()
                    document_id = cells[1].text.strip()
                    recording_date = cells[2].text.strip()
                    document_type = cells[3].text.strip()
                    document_name = cells[4].text.strip()
                    name_type = cells[5].text.strip()

                    # Do something with the extracted data, e.g., store it in a list or print it
                    print(item_number, document_id, recording_date, document_type, document_name, name_type)
            else:
                print("Results table not found inside printResults div.")
        else:
            print("printResults div not found.")
    else:
        print("Parent table not found.")


    # Prepare the CSV file to save results
    with open(f"{output_folder}/search_results.csv", mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Item#", "Document ID#", "Recording Date", "Document Type", "Document Name", "Name Type"])

        # Loop through each row and extract details
        for row in rows:
            cells = row.find_all("td")
            item_number = cells[0].text.strip()
            document_id = cells[1].text.strip()
            recording_date = cells[2].text.strip()
            document_type = cells[3].text.strip()
            document_name = cells[4].text.strip()
            name_type = cells[5].text.strip()

            # Convert the recording date to a datetime object for comparison
            try:
                record_date_obj = datetime.strptime(recording_date, "%m-%d-%Y %I:%M:%S %p")
            except ValueError:
                print(f"Skipping invalid date: {recording_date}")
                continue

            # Check if the recording date is within the specified range
            if start_date <= record_date_obj <= end_date:
                # Write the row to the CSV
                writer.writerow([item_number, document_id, recording_date, document_type, document_name, name_type])

                print(f"Extracted: {item_number}, {document_id}, {recording_date}, {document_type}, {document_name}, {name_type}")

                # Download associated files (PDFs, images, etc.) if available
                download_files(document_id, output_folder)

# Function to download files (PDFs, images, etc.)
def download_files(document_id, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    file_url = f"https://www.thecountyrecorder.com/Document.aspx?DK={document_id}"

    response = requests.get(file_url)
    if response.status_code == 200:
        file_name = os.path.join(output_folder, f"{document_id}.pdf")
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
        get_results_and_download(soup, output_folder, start_date, end_date)

# Ask user for input
def user_input():
    state = "COLORADO"
    county = "TELLER"
    start_date = "01-01-1931"
    end_date = "01-01-1960"
    output_folder = "output"
    return state, county, start_date, end_date, output_folder

# Main entry point
if __name__ == "__main__":
    state, county, start_date, end_date, output_folder = user_input()
    scrape(state, county, start_date, end_date, output_folder)
