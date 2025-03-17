import requests
from bs4 import BeautifulSoup

# Base URL
BASE_URL = "https://yumacountyaz-recweb.tylerhost.net/recorder/"
LOGIN_URL = f"{BASE_URL}web/loginPOST.jsp"
SEARCH_URL = f"{BASE_URL}eagleweb/docSearch.jsp"
SEARCH_RESULTS_URL = f"{BASE_URL}recorder/eagleweb/docSearchResults.jsp"

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
    # First, get the search page to extract any hidden fields or session parameters
    response = session.get(SEARCH_URL)
    if response.status_code != 200:
        print(f"Failed to load search page with status code {response.status_code}")
        return None
    
    # Parse the search page to get hidden form inputs (e.g., tokens, session data)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find any hidden inputs or tokens in the form
    hidden_inputs = soup.find_all('input', type='hidden')
    form_data = {input_tag['name']: input_tag['value'] for input_tag in hidden_inputs}
    
    # Add the actual search parameters to the form data
    form_data.update({
        "RecordingDateIDStart": start_date,
        "RecordingDateIDEnd": end_date,
        "searchType": "Search",  # Assuming 'Search' is the correct search button name
        "AllDocuments": "ALL",   # This ensures the "Search All Types" checkbox is checked
        "searchTerm": "lien",    # Adding "lien" as the search term
    })

    # Now, submit the form with the necessary data
    response = session.post(SEARCH_URL, data=form_data)
    
    if response.status_code == 200:
        print("Search submitted successfully.")
        # Check for the searchId in the response or redirect URL
        if "searchId=" in response.url:
            search_id = response.url.split("searchId=")[-1]
            print(f"Redirected to results with searchId: {search_id}")
            return search_id
        else:
            print("Failed to retrieve searchId from redirect URL.")
            return None
    else:
        print(f"Search failed with status code {response.status_code}")
        return None

# Step 3: Fetch the search results page using the searchId
def fetch_search_results(search_id):
    if search_id:
        results_url = f"{SEARCH_RESULTS_URL}?searchId={search_id}"
        response = session.get(results_url)
        
        if response.status_code == 200:
            print("Successfully fetched search results page.")
            print("HTML of the results page:")
            print(response.text)  # Print the HTML content of the search results page
            return response.text
        else:
            print(f"Failed to fetch results page with status code {response.status_code}")
            return None
    else:
        print("Invalid searchId. Cannot fetch results.")
        return None

# Step 4: Parse search results and get document links
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

# Step 5: Extract document details and download PDF
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

# Step 6: Download PDF
def download_pdf(pdf_url):
    pdf_response = session.get(pdf_url)
    if pdf_response.status_code == 200:
        filename = pdf_url.split('/')[-1]
        with open(filename, 'wb') as f:
            f.write(pdf_response.content)
        print(f"PDF downloaded: {filename}")
    else:
        print(f"Failed to download PDF: {pdf_url}")

# Main function to run the scraper
def main():
    if login():  # Step 1: Login
        search_id = search_documents("01/01/2024", "02/01/2024")  # Step 2: Search for documents
        if search_id:
            search_html = fetch_search_results(search_id)  # Step 3: Fetch the results page using searchId
            if search_html:
                # After printing the HTML, you can proceed to parse it
                document_links = parse_search_results(search_html)  # Step 4: Parse results and get links
                if document_links:
                    for doc_url in document_links:
                        doc_data = extract_document_data(doc_url)  # Step 5: Extract data for each document
                        if doc_data:
                            print(doc_data)  # You can save or process the data as needed
                else:
                    print("No document links found to process.")
            else:
                print("Failed to fetch search results page.")
        else:
            print("Failed to perform search.")
    else:
        print("Login failed. Exiting scraper.")

if __name__ == "__main__":
    main()
