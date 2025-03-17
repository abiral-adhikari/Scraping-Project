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
    
    response = session.get(search_url)
    if response.status_code != 200:
        print("Failed to load search page.")
        return None
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Extract hidden fields for form submission
    viewstate = soup.find("input", {"name": "__VIEWSTATE"})["value"]
    eventvalidation = soup.find("input", {"name": "__EVENTVALIDATION"})["value"]
    
    # Correct value for 'Lien' document group
    lien_value = "3|Lien"
    
    form_data = {
        "__VIEWSTATE": viewstate,
        "__EVENTVALIDATION": eventvalidation,
        "ctl00$ctl00$MainContent$searchMainContent$ctl00$cboDocumentGroup": lien_value,
        "ctl00$ctl00$MainContent$searchMainContent$ctl00$tbDateStart": start_date,
        "ctl00$ctl00$MainContent$searchMainContent$ctl00$tbDateEnd": end_date,
        "ctl00$ctl00$MainContent$searchMainContent$ctl00$btnSearchDocuments": "Execute Search"
    }
    
    response = session.post(search_url, data=form_data)
    if response.status_code == 200:
        print("Search executed successfully.")
        return response.text
    else:
        print("Failed to execute search.")
        return None

# Function to parse results and download files
def get_results_and_download(soup, output_folder, start_date, end_date):
    print("Parsing search results...")

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    parent_table = soup.find("table", id="tableMain")
    if parent_table:
        print("Parent table found")

        table_content = parent_table.find("td", id="tableMain_Content")
        if table_content:
            print("Found tableMain_Content td")

            main_div = table_content.find("div", class_="main")
            if main_div:
                print("Found div.main")

                print_results_div = main_div.find("div", id="PrintResults")
                if print_results_div:
                    print("Found PrintResults div")

                    results_table = print_results_div.find("table", class_="Results")
                    if results_table:
                        print("Found results table")
                        rows = results_table.find_all("tr", class_=["results-data-row", "results-data-row listitem-background-color2", "results-data-row listitem-background-color1"])

                        # Convert start_date and end_date to datetime.date objects
                        try:
                            start_date_obj = datetime.strptime(start_date, "%m-%d-%Y").date()
                            end_date_obj = datetime.strptime(end_date, "%m-%d-%Y").date()
                        except ValueError:
                            print(f"Invalid date format for start_date or end_date. Please use MM-DD-YYYY.")
                            return

                        # Prepare to write results and image links
                        with open(f"{output_folder}/search_results.csv", mode='w', newline='', encoding='utf-8') as file:
                            writer = csv.writer(file)
                            writer.writerow(["Item#", "Document ID#", "Recording Date", "Document Type", "Document Name", "Name Type"])

                            with open(f"{output_folder}/image_links.csv", mode='w', newline='', encoding='utf-8') as img_file:
                                img_writer = csv.writer(img_file)
                                img_writer.writerow(["Item#", "Document ID#", "Image URL"])

                                for row in rows:
                                    cells = row.find_all("td")
                                    if len(cells) < 6:
                                        print("Skipping row with insufficient columns")
                                        continue

                                    item_number = cells[0].text.strip()
                                    document_id = cells[1].text.strip()
                                    recording_date = cells[2].text.strip()
                                    document_type = cells[3].text.strip()
                                    document_name = cells[4].text.strip()
                                    name_type = cells[5].text.strip()

                                    try:
                                        # Try parsing with time
                                        record_date_obj = datetime.strptime(recording_date, "%m-%d-%Y %I:%M:%S %p").date()
                                    except ValueError:
                                        try:
                                            # Try parsing without time
                                            record_date_obj = datetime.strptime(recording_date, "%m-%d-%Y").date()
                                        except ValueError:
                                            print(f"Skipping invalid date: {recording_date}")
                                            continue  # Skip this row if both fail

                                    # Compare the record date with the start and end dates
                                    if start_date_obj <= record_date_obj <= end_date_obj:
                                        writer.writerow([item_number, document_id, recording_date, document_type, document_name, name_type])
                                        print(f"Extracted: {item_number}, {document_id}, {recording_date}, {document_type}, {document_name}, {name_type}")

                                        # Check if an image is available and download it
                                        image_url = get_image_url(session, document_id, output_folder)
                                        if image_url:
                                            img_writer.writerow([item_number, document_id, image_url])
                                            download_image(image_url, document_id, output_folder)

# Function to extract image URL if available

def get_image_url(session, document_id, output_folder):
    download_all_pages(session, document_id, output_folder)

# Function to download the image
def download_image(image_url, document_id, output_folder):
    print(f"Attempting to download image from {image_url}")
    response = requests.get(image_url)
    if response.status_code == 200:
        file_name = os.path.join(output_folder, f"{document_id}_image.jpg")
        with open(file_name, 'wb') as file:
            file.write(response.content)
        print(f"Downloaded image {file_name}")
    else:
        print(f"Failed to download image from {image_url}")

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
    county = "BACA"
    start_date = "01-01-2019"
    end_date = "01-01-2025"
    output_folder = "output"
    return state, county, start_date, end_date, output_folder


def download_all_pages(session, document_id, output_folder):
    image_page_url = f"{BASE_URL}/Image.aspx?DK={document_id}&PN=1"
    response = session.get(image_page_url)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        page_count_tag = soup.find("span", {"id": "MainContent_searchMainContent_ctl00_lblPageCount"})
        
        if page_count_tag:
            page_count = int(page_count_tag.text.strip().split(" ")[-1])
            for page_num in range(1, page_count + 1):
                image_tag = soup.find("img", {"id": "MainContent_searchMainContent_ctl00_Image2"})
                if image_tag:
                    image_src = image_tag["src"]
                    image_url = f"{BASE_URL}/{image_src}"
                    
                    image_response = session.get(image_url)
                    if image_response.status_code == 200:
                        file_name = os.path.join(output_folder, f"{document_id}_page_{page_num}.jpg")
                        with open(file_name, 'wb') as file:
                            file.write(image_response.content)
                        print(f"Downloaded {file_name}")
                    else:
                        print(f"Failed to download image from {image_url}")
                
                # Click next page if not the last page
                if page_num < page_count:
                    next_button = soup.find("input", {"id": "MainContent_searchMainContent_ctl00_btnNext"})
                    if next_button and "disabled" not in next_button.attrs:
                        session.post(image_page_url, data={"ctl00$ctl00$MainContent$searchMainContent$ctl00$btnNext": "Next Page"})
                        response = session.get(image_page_url)
                        soup = BeautifulSoup(response.text, 'html.parser')
    else:
        print(f"Failed to load image page for document {document_id}")

# Main entry point
if __name__ == "__main__":
    state, county, start_date, end_date, output_folder = user_input()
    scrape(state, county, start_date, end_date, output_folder)
