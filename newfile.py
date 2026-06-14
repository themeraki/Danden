import requests
from datetime import datetime

# 1. Setup the URL (This usually changes daily)
today = datetime.now().strftime("%d-%m-%Y")
# Note: This URL is an example; you'll need the actual endpoint from the site
pdf_url = f"https://epaper.thehindu.com/pdf/{today}/daily_edition.pdf"

# 2. Your 'Secret' Headers
# You MUST copy these from your browser after logging in manually
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Cookie": "SESSION_ID=your_actual_cookie_data_here; USER_AUTH=your_auth_token",
    "Referer": "https://epaper.thehindu.com/"
}

def download_paper():
    print(f"Attempting to download paper for {today}...")
    
    # 3. Make the request
    response = requests.get(pdf_url, headers=headers, stream=True)

    # 4. Check if it worked
    if response.status_code == 200:
        with open(f"The_Hindu_{today}.pdf", "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print("Success! PDF saved.")
    elif response.status_code == 403:
        print("Error: Access Denied. Your Cookies are probably expired or invalid.")
    else:
        print(f"Failed. Status Code: {response.status_code}")

if __name__ == "__main__":
    download_paper()
