import requests
from bs4 import BeautifulSoup
import os

# Constants
LOGIN_URL = "https://yumacountyaz-recweb.tylerhost.net/recorder/web/login.jsp"
SEARCH_URL = "https://yumacountyaz-recweb.tylerhost.net/recorder/eagleweb/docSearch.jsp"
START_DATE = "01/01/2024"
END_DATE = "12/31/2024"
DOWNLOAD_DIR = "downloads"

# Function to download PDF
def download_pdf(pdf_url):
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)
    response = requests.get(pdf_url)
    pdf_name = os.path.join(DOWNLOAD_DIR, pdf_url.split('/')[-1])
    with open(pdf_name, 'wb') as f:
        f.write(response.content)
    print(f'Downloaded: {pdf_name}')

# Function to log in
def login(session):
    payload = {
        'submit': 'Public Login',  # This is the value of the submit button
        # Add any other required fields for login here if necessary
    }
    response = session.post(LOGIN_URL, data=payload)
    return response.status_code == 200  # Return True if login was successful

# Function to scrape the website
def scrape_yuma_county():
    # Start a session
    session = requests.Session()
    
    # Log in to the website
    if not login(session):
        print("Login failed!")
        return
    
    # Define the search parameters
    payload = {
        'RecordingDateIDStart': START_DATE,
        'RecordingDateIDEnd': END_DATE,
        'documentType': 'Lien',  # Adjust this based on the actual form field name
        'search': 'Search'  # Adjust this based on the actual form field name
    }
    
    # Send a POST request to the search endpoint
    response = session.post(SEARCH_URL, data=payload)
    
    # Check if the request was successful
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the search results
        results = soup.find_all('tr', class_='searchResultRow')  # Adjust the selector based on actual HTML structure
        
        for row in results:
            details = [cell.text for cell in row.find_all('td')]  # Extract details from each cell
            
            # Extract PDF link
            pdf_link = row.find('a', href=True)
            if pdf_link and 'viewPdf' in pdf_link['href']:
                pdf_url = pdf_link['href']
                download_pdf(pdf_url)
            else:
                pdf_url = "No PDF Available"
            
            print(details + [pdf_url])  # Print or store the extracted data as needed
    else:
        print(f'Failed to retrieve data: {response.status_code}')

if __name__ == '__main__':
    scrape_yuma_county()