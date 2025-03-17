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

# Set initial cookies manually
session.cookies.set("isLoggedInAsPublic", "true", domain="yumacountyaz-recweb.tylerhost.net", path="/recorder")
session.cookies.set("pageSize", "100", domain="yumacountyaz-recweb.tylerhost.net", path="/recorder/eagleweb")
session.cookies.set("sortDir", "asc", domain="yumacountyaz-recweb.tylerhost.net", path="/recorder/eagleweb")
session.cookies.set("sortField", "Document+Id", domain="yumacountyaz-recweb.tylerhost.net", path="/recorder/eagleweb")

# Step 1: Log in as a guest user
def login():
    login_data = {"submit": "Public Login", "guest": "true"}
    response = session.post(LOGIN_URL, data=login_data)
    if response.status_code == 200:
        print("Login successful")
    else:
        print(f"Login failed with status code {response.status_code}")
        return False
    return True

# Step 2: Mimic the XHR request to get the requestId
def fetch_xhr_data(start_date, end_date):
    xhr_url = urljoin(BASE_URL, "ajaxSearchInit.jsp")
    xhr_data = {"RecordingDateIDStart": start_date, "RecordingDateIDEnd": end_date, "searchType": "search", "AllDocuments": "ALL"}
    xhr_response = session.post(xhr_url, data=xhr_data)
    if xhr_response.status_code == 200:
        data = xhr_response.json()
        request_id = data.get("requestId")
        print(f"Received requestId: {request_id}")
        return request_id
    else:
        print(f"XHR request failed with status {xhr_response.status_code}")
        return None

# Step 3: Perform the search
def search_documents(start_date, end_date):
    request_id = fetch_xhr_data(start_date, end_date)
    search_data = {"RecordingDateIDStart": start_date, "RecordingDateIDEnd": end_date, "searchType": "search", "AllDocuments": "ALL", "Search": "Search", "requestId": request_id}
    response = session.post(SEARCH_URL, data=search_data, allow_redirects=False)
    if response.status_code in [301, 302]:
        relative_redirect_url = response.headers.get("Location").lstrip("../")
        redirect_url = urljoin(BASE_URL, relative_redirect_url)
        search_id = redirect_url.split("searchId=")[-1]
        print(f"Extracted searchId: {search_id}")
        results_response = session.get(redirect_url)
        return results_response.text if results_response.status_code == 200 else None
    else:
        print(f"Search failed with status code {response.status_code}")
        return None

# Step 4: Parse search results
def parse_search_results(search_html):
    soup = BeautifulSoup(search_html, 'html.parser')
    results = []
    rows = soup.find_all('tr', {'class': 'clickable'})
    for row in rows:
        link = row.find('a', href=True)
        if link and "viewDoc.jsp" in link['href']:
            document_url = BASE_URL + link['href']
            results.append(document_url)
    return results

# Step 5: Extract document details and download PDF
def extract_document_data(doc_url):
    response = session.get(doc_url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
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
        pdf_link = soup.find('a', text='Download PDF')
        if pdf_link and 'href' in pdf_link.attrs:
            doc_details['PDF URL'] = BASE_URL + pdf_link['href']
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

# Main function
def main():
    if login():
        search_html = search_documents("01/01/2024", "02/25/2024")
        if search_html:
            document_links = parse_search_results(search_html)
            for doc_url in document_links:
                doc_data = extract_document_data(doc_url)
                if doc_data:
                    print(doc_data)
        else:
            print("Failed to perform search.")
    else:
        print("Login failed. Exiting scraper.")

if __name__ == "__main__":
    main()
