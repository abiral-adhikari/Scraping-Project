import os
import time
import csv
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

# Configure the browser for selenium
def create_driver():
    options = Options()
    options.add_argument("--headless")  # Run headlessly
    # Automatically download ChromeDriver if not installed
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

# Function to set up state, county, date range, and document group
def setup_search(driver, state, county, start_date, end_date):
    # Navigate to the website
    driver.get("https://thecountyrecorder.com")
    
    # Select the state
    state_select = Select(driver.find_element(By.ID, "MainContent_searchMainContent_ctl01_ctl00_cboStates"))
    # State mapping to the correct value
    state_map = {
        'ARIZONA': '-1|AZ',
        'COLORADO': '-1|CO'
    }
    
    if state.upper() in state_map:
        state_select.select_by_value(state_map[state.upper()])
    else:
        print(f"State {state} not found in options.")
        driver.quit()
        return None
    
    # Select the county
    county_select = Select(driver.find_element(By.ID, "MainContent_searchMainContent_ctl01_ctl00_cboCounties"))  # Update with correct ID for county
    county_select.select_by_visible_text(county)  # Select county based on visible text

    # Set the date range (start and end dates)
    start_date_input = driver.find_element(By.ID, "start_date")  # Update with correct ID for start date
    end_date_input = driver.find_element(By.ID, "end_date")  # Update with correct ID for end date
    start_date_input.clear()
    start_date_input.send_keys(start_date)
    end_date_input.clear()
    end_date_input.send_keys(end_date)
    
    # Select the "Lien" document group
    lien_checkbox = driver.find_element(By.ID, "lien")  # Update with correct ID for lien checkbox
    if not lien_checkbox.is_selected():
        lien_checkbox.click()

# Function to get the search results and download the images/PDFs
def get_results_and_download(driver, output_folder):
    # Trigger the search (after selecting the state, county, date range)
    search_button = driver.find_element(By.ID, "search_button")  # Update with correct ID for the search button
    search_button.click()

    time.sleep(5)  # Wait for results to load

    # Parse the search results page
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    # Extracting details from the search results
    records = soup.find_all("div", class_="record")  # Update with the correct HTML class
    
    # Prepare CSV file to store results
    with open(f"{output_folder}/search_results.csv", mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Document ID", "Title", "Date", "Lien Type", "URL"])  # Add necessary columns

        # Loop through each record and extract details
        for record in records:
            doc_id = record.find("span", class_="doc_id").text  # Update with correct HTML class/tag
            title = record.find("span", class_="title").text  # Update with correct HTML class/tag
            date = record.find("span", class_="date").text  # Update with correct HTML class/tag
            lien_type = record.find("span", class_="lien_type").text  # Update with correct HTML class/tag
            doc_url = record.find("a", class_="doc_url")["href"]  # Update with correct HTML tag

            # Write record details to CSV
            writer.writerow([doc_id, title, date, lien_type, doc_url])
            
            # Download images/PDFs (example, needs to be adjusted based on the HTML structure)
            download_files(doc_url, output_folder)

# Function to download the files (images or PDFs)
def download_files(doc_url, output_folder):
    # Ensure output folder exists
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # Download the file (images/PDFs)
    response = requests.get(doc_url)
    file_name = os.path.join(output_folder, doc_url.split("/")[-1])
    
    with open(file_name, 'wb') as file:
        file.write(response.content)
    
    print(f"Downloaded {file_name}")

# Main function to scrape
def scrape(state, county, start_date, end_date, output_folder):
    driver = create_driver()
    try:
        setup_search(driver, state, county, start_date, end_date)
        get_results_and_download(driver, output_folder)
    finally:
        driver.quit()

# Ask user for input
def user_input():
    state = input("Enter the state (e.g., ARIZONA, COLORADO): ")
    county = input("Enter the county: ")
    start_date = input("Enter the start date (MM/DD/YYYY): ")
    end_date = input("Enter the end date (MM/DD/YYYY): ")
    output_folder = input("Enter the folder name for saving results: ")

    return state, county, start_date, end_date, output_folder

# Main entry point
if __name__ == "__main__":
    state, county, start_date, end_date, output_folder = user_input()
    scrape(state, county, start_date, end_date, output_folder)
