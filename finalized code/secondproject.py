import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
# Base URL
BASE_URL = "https://yumacountyaz-recweb.tylerhost.net/recorder/"
LOGIN_URL = f"{BASE_URL}web/loginPOST.jsp"
SEARCH_URL = f"{BASE_URL}eagleweb/docSearchPOST.jsp"
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

# # Step 2: Search with filters (date range and "lien" in the search term)
# def search_documents(start_date, end_date):
#     search_data = {
#         "RecordingDateIDStart": start_date,
#         "RecordingDateIDEnd": end_date,
#         "GrantorIDSearchType":"Basic Searching",
#         "BothNamesIDSearchType":"Basic Searching",
#         "GranteeIDSearchType":"Basic Searching",
#         "Search":"search",
#         "AllDocuments": "ALL",   # This ensures the "Search All Types" checkbox is checked
#     }
#     response = session.post(SEARCH_URL, data=search_data)
    
#     if response.status_code == 200:
#         print("Search successful")
#         print("HTML of the search page:")
#         # print(response.text)  # Print the HTML content of the search page
#         return response.text
#     else:
#         print(f"Search failed with status code {response.status_code}")
#         return None

# Step 1: Mimic the XHR request to get the requestId
def fetch_xhr_data(start_date, end_date):
    xhr_url = urljoin(BASE_URL, "ajaxSearchInit.jsp")  # Replace with the correct XHR endpoint URL
    xhr_data = {
        "RecordingDateIDStart": start_date,
        "RecordingDateIDEnd": end_date,
        "searchType": "search",
        "AllDocuments": "ALL",
    }
    # Send the XHR request
    
    xhr_response = session.post(xhr_url, data=xhr_data)

    if xhr_response.status_code == 200:
        # Assuming the XHR response contains the requestId or a token
        data = xhr_response.json()  # Check the response format
        request_id = data.get("requestId")  # Extract the requestId from the response
        print(f"Received requestId: {request_id}")
        return request_id
    else:
        print(f"XHR request failed with status {xhr_response.status_code}")
        return None

# Step 2: Perform the search
def search_documents(start_date, end_date):
    request_id = fetch_xhr_data(start_date, end_date)
    search_data = {
        "RecordingDateIDStart": start_date,
        "RecordingDateIDEnd": end_date,
        "searchType": "search",
        "AllDocuments": "ALL",
        "Search": "Search",  # Simulating button click
        "requestId": request_id  # Include the requestId from the XHR
    }

    response = session.post(SEARCH_URL, data=search_data, allow_redirects=False)

    if response.status_code in [301, 302]:  # Redirect detected
        relative_redirect_url = response.headers.get("Location")  # Example: ../eagleweb/docSearchResults.jsp?searchId=1
        relative_redirect_url = relative_redirect_url.lstrip("../")  # Remove leading ../
        redirect_url = urljoin(BASE_URL, relative_redirect_url)  # Convert to full URL

        # Extract searchId
        if "searchId=" in redirect_url:
            search_id = redirect_url.split("searchId=")[-1]
            print(f"Extracted searchId: {search_id}")
        else:
            print("Error: searchId not found in redirect URL.")
            return None

        # Fetch search results
        print(f"Redirecting to results: {redirect_url}")
        results_response = session.get(redirect_url)

        if results_response.status_code == 200:
            print("Search results fetched successfully")
            return results_response.text  # Return HTML of results page
        else:
            print(f"Failed to fetch results: {results_response.status_code}")
            return None
    else:
        print(f"Search failed with status code {response.status_code}")
        return None


    
# Step 3: Parse search results and get document links
def parse_search_results(search_html):
    soup = BeautifulSoup(search_html, 'html.parser')
    # print(soup)
    results = []
    # Looking for the table rows that contain clickable document links
    rows = soup.find_all('tr', {'class': 'clickable'})
    print(rows)
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

# Main function to run the scraper
def main():
    if login():  # Step 1: Login
        search_html = search_documents("01/01/2024", "02/25/2024")  # Step 2: Search for documents
        if search_html:
            # After printing the HTML, you can proceed to parse it
            document_links = parse_search_results(search_html)  # Step 3: Parse results and get links
            if document_links:
                for doc_url in document_links:
                    doc_data = extract_document_data(doc_url)  # Step 4: Extract data for each document
                    if doc_data:
                        print(doc_data)  # You can save or process the data as needed
            else:
                print("No document links found to process.")
        else:
            print("Failed to perform search.")
    else:
        print("Login failed. Exiting scraper.")

if __name__ == "__main__":
    main()
