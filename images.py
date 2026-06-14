import requests
from bs4 import BeautifulSoup
import base64
import csv
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- CONFIGURATION ---
BASE_URL = "https://theedenschool.in/birth_certificate.php"
OUTPUT_FILE = "eden_school_data.csv"
PHOTO_FOLDER = "student_photos"
START_ID = 0
END_ID = 800
MAX_WORKERS = 8 

# Ensure the photo folder exists
if not os.path.exists(PHOTO_FOLDER):
    os.makedirs(PHOTO_FOLDER)

def get_b64_id(number):
    return base64.b64encode(str(number).encode()).decode()

def download_image(url, scholar_no):
    """Downloads an image and saves it as scholar_no.jpg"""
    try:
        if not url or url == "N/A":
            return "N/A"
        
        # Clean URL if it's relative
        if url.startswith('http') == False:
            url = "https://theedenschool.in/schoolerp/" + url

        img_data = requests.get(url, timeout=10).content
        filename = f"{scholar_no}.jpg"
        filepath = os.path.join(PHOTO_FOLDER, filename)
        
        with open(filepath, 'wb') as f:
            f.write(img_data)
        return filename
    except:
        return "Error"

def scrape_single_id(student_id):
    b64_val = get_b64_id(student_id)
    params = {'stuid': b64_val}
    
    try:
        response = requests.get(BASE_URL, params=params, timeout=5)
        if response.status_code == 200 and "Scholar No" in response.text:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            def get_val(label):
                tag = soup.find('strong', string=lambda x: x and label in x)
                return tag.get_text(strip=True).split(':')[-1].strip() if tag else "N/A"

            scholar_no = get_val("Scholar No")
            name = get_val("Name")
            
            # Find Image URL
            img_tag = soup.find('img', src=lambda x: x and 'uploads' in x)
            remote_img_url = img_tag['src'] if img_tag else "N/A"
            
            # Download the image locally
            local_img_name = "N/A"
            if remote_img_url != "N/A":
                local_img_name = download_image(remote_img_url, scholar_no)

            return {
                "System_ID": student_id,
                "Scholar No": scholar_no,
                "Class": get_val("Class"),
                "Name": name,
                "Father Name": get_val("Father Name"),
                "Mother Name": get_val("Mother Name"),
                "Image Filename": local_img_name
            }, student_id
    except:
        pass
    return None, student_id

def main():
    fieldnames = ["System_ID", "Scholar No", "Class", "Name", "Father Name", "Mother Name", "Image Filename"]
    
    print(f"🚀 Launching Scraper + Image Downloader... (0 to 800)")
    
    valid_count = 0
    with open(OUTPUT_FILE, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_id = {executor.submit(scrape_single_id, i): i for i in range(START_ID, END_ID + 1)}
            
            for future in as_completed(future_to_id):
                result, s_id = future.result()
                
                if result:
                    writer.writerow(result)
                    valid_count += 1
                    print(f"📸 Saved: {result['Name']} (Img: {result['Image Filename']})")
                elif s_id % 50 == 0:
                    print(f"📡 Processing... currently at ID {s_id}")

    print(f"\n✨ FINISHED!")
    print(f"📊 Records: {valid_count} | 📂 Photos: check '{PHOTO_FOLDER}' folder")

if __name__ == "__main__":
    main()
