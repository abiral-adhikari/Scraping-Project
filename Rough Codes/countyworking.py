import os
import requests
from bs4 import BeautifulSoup
import csv
from datetime import datetime

BASE_URL = "https://www.thecountyrecorder.com"

# Function to select state
def select_state(session, state):
    response = session.get(BASE_URL)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract hidden fields for form submission
        viewstate = soup.find("input", {"name": "__VIEWSTATE"})["value"]
        eventvalidation = soup.find("input", {"name": "__EVENTVALIDATION"})["value"]

        # Ensure we send the correct state value (confirm state value matches the options)
        state_dropdown = soup.find("select", {"id": "MainContent_searchMainContent_ctl01_ctl00_cboStates"})
        state_value = None
        for option in state_dropdown.find_all("option"):
            if option.text.strip().upper() == state.upper():
                state_value = option['value']
                break

        if not state_value:
            print(f"State '{state}' not found!")
            return False

        form_data = {
            "__VIEWSTATE": viewstate,
            "__EVENTVALIDATION": eventvalidation,
            "ctl00$ctl00$MainContent$searchMainContent$ctl01$ctl00$cboStates": state_value,
            "ctl00$ctl00$MainContent$searchMainContent$ctl01$ctl00$btnChangeCounty": "Go"
        }

        post_response = session.post(BASE_URL, data=form_data)
        if post_response.status_code == 200:
            print(f"State '{state}' selected successfully.")
            return True
        else:
            print("Failed to select state.")
            return False
    return False

# Function to select county
def select_county(session, county):
    response = session.get(BASE_URL)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract hidden fields for form submission
        viewstate = soup.find("input", {"name": "__VIEWSTATE"})["value"]
        eventvalidation = soup.find("input", {"name": "__EVENTVALIDATION"})["value"]

        # Ensure we send the correct county value (confirm county value matches the options)
        county_dropdown = soup.find("select", {"id": "MainContent_searchMainContent_ctl01_ctl00_cboCounties"})
        county_value = None
        for option in county_dropdown.find_all("option"):
            if option.text.strip().upper() == county.upper():
                county_value = option['value']
                break

        if not county_value:
            print(f"County '{county}' not found!")
            return False

        form_data = {
            "__VIEWSTATE": viewstate,
            "__EVENTVALIDATION": eventvalidation,
            "ctl00$ctl00$MainContent$searchMainContent$ctl01$ctl00$cboCounties": county_value,
            "ctl00$ctl00$MainContent$searchMainContent$ctl01$ctl00$btnChangeCounty": "Go"
        }

        post_response = session.post(BASE_URL, data=form_data)
        if post_response.status_code == 200:
            print(f"County '{county}' selected successfully.")
            return True
        else:
            print("Failed to select county.")
            return False
    return False

# Function to accept the disclaimer and navigate to the search page
def accept_disclaimer(session):
    disclaimer_url = f"{BASE_URL}/Disclaimer.aspx?RU=%2FIntroduction.aspx"
    
    response = session.get(disclaimer_url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')

        form_action = soup.find("form")["action"]

        form_data = {
            "ctl00$ctl00$MainContent$searchMainContent$ctl01$btnAccept": "Yes, I Accept"
        }

        post_response = session.post(f"{BASE_URL}{form_action}", data=form_data)
        if post_response.status_code == 200:
            print("Disclaimer accepted. Redirecting to search page...")
            
            # After accepting the disclaimer, we now follow the search link.
            search_url = f"{BASE_URL}/Search.aspx"
            response = session.get(search_url)
            if response.status_code == 200:
                print("Search page loaded successfully.")
                return True
            else:
                print("Failed to load search page.")
                return False
        else:
            print("Failed to accept disclaimer.")
            return False
    return False

# Function to set up the search form
def setup_search(session, state, county, start_date, end_date):
    search_url = f"{BASE_URL}/Search.aspx"
    
    form_data = {
        'ctl00$ctl00$MainContent$searchMainContent$ctl01$ctl00$cboStates': state,
        'ctl00$ctl00$MainContent$searchMainContent$ctl01$ctl00$cboCounties': county,
        'ctl00$ctl00$MainContent$searchMainContent$ctl00$tbDateStart': start_date,
        'ctl00$ctl00$MainContent$searchMainContent$ctl00$tbDateEnd': end_date,
        'ctl00$ctl00$MainContent$searchMainContent$ctl01$ctl00$DocumentGroup': 'Lien',
        'ctl00$ctl00$MainContent$searchMainContent$ctl01$ctl00$btnSearch': 'Search'
    }

    response = session.post(search_url, data=form_data)
    if response.status_code == 200:
        print("Search form submitted successfully.")
        return response.text
    else:
        print("Failed to submit search form.")
        return None

# Function to parse results and download files
def get_results_and_download(soup, output_folder, start_date, end_date):
    print("Parsing search results...")

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    parent_table = soup.find("table", id="tableMain")
    if parent_table:
        print(parent_table)
        print_results_div = parent_table.find("div", id="PrintResults")
        
        if print_results_div:
            results_table = print_results_div.find("table", id="MainContent_searchMainContent_ctl00_Table2", class_="Results")
            
            if results_table:
                rows = results_table.find_all("tr", class_=["results-data-row", "results-data-row listitem-background-color2", "results-data-row listitem-background-color1"])
                
                with open(f"{output_folder}/search_results.csv", mode='w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    writer.writerow(["Item#", "Document ID#", "Recording Date", "Document Type", "Document Name", "Name Type"])

                    for row in rows:
                        cells = row.find_all("td")
                        item_number = cells[0].text.strip()
                        document_id = cells[1].text.strip()
                        recording_date = cells[2].text.strip()
                        document_type = cells[3].text.strip()
                        document_name = cells[4].text.strip()
                        name_type = cells[5].text.strip()

                        try:
                            record_date_obj = datetime.strptime(recording_date, "%m-%d-%Y %I:%M:%S %p")
                        except ValueError:
                            print(f"Skipping invalid date: {recording_date}")
                            continue

                        if start_date <= record_date_obj <= end_date:
                            writer.writerow([item_number, document_id, recording_date, document_type, document_name, name_type])
                            print(f"Extracted: {item_number}, {document_id}, {recording_date}, {document_type}, {document_name}, {name_type}")
                            download_files(document_id, output_folder)
            else:
                print("Results table not found.")
        else:
            print("printResults div not found.")
    else:
        print("Parent table not found.")

# Function to download files
def download_files(document_id, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    file_url = f"{BASE_URL}/Document.aspx?DK={document_id}"

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

    if not select_state(session, state):
        return
    if not select_county(session, county):
        return
    if not accept_disclaimer(session):
        return
    
    search_page_html = setup_search(session, state, county, start_date, end_date)
    
    if search_page_html:
        soup = BeautifulSoup(search_page_html, 'html.parser')
        get_results_and_download(soup, output_folder, start_date, end_date)

# User input
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
