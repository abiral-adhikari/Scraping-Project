import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

# Base URL
BASE_URL = "https://yumacountyaz-recweb.tylerhost.net/recorder/"
LOGIN_URL = f"{BASE_URL}web/loginPOST.jsp"
SEARCH_URL = f"{BASE_URL}eagleweb/docSearch.jsp"
DOCUMENT_URL = f"{BASE_URL}recorder/eagleweb/viewDoc.jsp"

# Create a session to persist login state
session = requests.Session()

# Step 1: Log in as a guest user
def login():
    login_data = {
        "submit": "Public Login",
        "guest": "true",
    }
    response = session.post(LOGIN_URL, data=login_data)
    
    if response.status_code == 200:
        print("Login successful")
    else:
        print(f"Login failed with status code {response.status_code}")
        print(response.text)  # To see the page content for debugging
        return False
    return True

# Step 2: Search with filters (date range and "lien" in the search term)
def search_documents(start_date, end_date):
    # Add any hidden fields you find during inspection
    search_data = {
        "RecordingDateIDStart": start_date,
        "RecordingDateIDEnd": end_date,
        "searchType": "Search",  # Assuming 'Search' is the correct search button name
        "AllDocuments": "ALL",   # This ensures the "Search All Types" checkbox is checked
        
        # Hidden fields (you need to inspect the form and add these if required)
        "hiddenFieldName": "hiddenValue",  # Example hidden field
    }

    # Set headers to mimic a browser request
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    response = session.post(SEARCH_URL, data=search_data, headers=headers)
    
    if response.status_code == 200:
        print(f"Search successful for range {start_date} to {end_date}")
        # Save the response HTML to a file for debugging if needed
        with open("search_results.html", "w", encoding="utf-8") as file:
            file.write(response.text)
        
        # You can also print the response content directly if you want to see it in the console
        print(response.text)
        return response.text
    else:
        print(f"Search failed with status code {response.status_code} for range {start_date} to {end_date}")
        print(response.text)  # Print the full HTML to understand the issue
        return None

# Step 3: Parse search results and get document links
def parse_search_results(search_html):
    soup = BeautifulSoup(search_html, 'html.parser')
    results = []
    
    # Looking for the table rows that contain clickable document links
    rows = soup.find_all('tr', {'class': 'clickable'})
    if not rows:
        print("No results found in the search page.")
        return results
    
    for row in rows:
        link = row.find('a', href=True)
        if link and "viewDoc.jsp" in link['href']:
            document_url = BASE_URL + link['href']
            results.append(document_url)
    
    if not results:
        print("No document links found.")
    return results

# Step 4: Extract document details and download PDF
def extract_document_data(doc_url):
    response = session.get(doc_url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extracting document details
        doc_details = {}
        grantor_tag = soup.find('span', text='Grantor:')
        if grantor_tag:
            doc_details['Grantor'] = grantor_tag.find_next('span').text.strip()
        
        grantee_tag = soup.find('span', text='Grantee:')
        if grantee_tag:
            doc_details['Grantee'] = grantee_tag.find_next('span').text.strip()

        recording_date_tag = soup.find('span', text='Recording Date')
        if recording_date_tag:
            doc_details['Recording Date'] = recording_date_tag.find_next('span').text.strip()

        # Extract PDF link
        pdf_link = soup.find('a', text='Download PDF')
        if pdf_link and 'href' in pdf_link.attrs:
            doc_details['PDF URL'] = BASE_URL + pdf_link['href']
            # Download the PDF
            download_pdf(doc_details['PDF URL'])
        
        return doc_details
    else:
        print(f"Failed to fetch document data for {doc_url} with status code {response.status_code}")
        return None

# Step 5: Download PDF
def download_pdf(pdf_url):
    pdf_response = session.get(pdf_url)
    if pdf_response.status_code == 200:
        filename = pdf_url.split('/')[-1]
        with open(filename, 'wb') as f:
            f.write(pdf_response.content)
        print(f"PDF downloaded: {filename}")
    else:
        print(f"Failed to download PDF: {pdf_url}")

# Helper function to generate date ranges for each month
def generate_monthly_date_ranges(start_date, end_date):
    start_date = datetime.strptime(start_date, "%m/%d/%Y")
    end_date = datetime.strptime(end_date, "%m/%d/%Y")
    
    date_ranges = []
    
    while start_date < end_date:
        # Get the first and last day of the current month
        first_day = start_date.replace(day=1)
        next_month = first_day.replace(day=28) + timedelta(days=4)  # Move to the next month
        last_day = next_month - timedelta(days=next_month.day)
        
        # Ensure last day does not exceed the end date
        if last_day > end_date:
            last_day = end_date
        
        # Append the range as a tuple (start, end)
        date_ranges.append((first_day.strftime("%m/%d/%Y"), last_day.strftime("%m/%d/%Y")))
        
        # Move to the next month
        start_date = last_day + timedelta(days=1)
    
    return date_ranges

# Main function to run the scraper
def main():
    start_date = "01/01/2024"
    end_date = "12/31/2024"
    
    # Generate the monthly date ranges
    date_ranges = generate_monthly_date_ranges(start_date, end_date)
    
    if login():  # Step 1: Login
        for start, end in date_ranges:
            search_html = search_documents(start, end)  # Step 2: Search for documents by month
            if search_html:
                # After printing the HTML, you can proceed to parse it
                document_links = parse_search_results(search_html)  # Step 3: Parse results and get links
                if document_links:
                    for doc_url in document_links:
                        doc_data = extract_document_data(doc_url)  # Step 4: Extract data for each document
                        if doc_data:
                            print(doc_data)  # You can save or process the data as needed
                else:
                    print(f"No document links found for the range {start} to {end}.")
            else:
                print(f"Failed to perform search for the range {start} to {end}.")
    else:
        print("Login failed. Exiting scraper.")

if __name__ == "__main__":
    main()
