import requests
from bs4 import BeautifulSoup
import base64
import csv
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- CONFIGURATION ---
BASE_URL = "https://theedenschool.in/birth_certificate.php"
OUTPUT_FILE = "eden_school_data.txt"  # Changed to .txt
PHOTO_FOLDER = "student_photos"
START_ID = 0
END_ID = 800
MAX_WORKERS = 8 

# Ensure the photo folder exists
if not os.path.exists(PHOTO_FOLDER):
    os.makedirs(PHOTO_FOLDER)

def get_b64_id(number):
    return base64.b64encode(str(number).encode()).decode()

def sanitize_filename(name):
    """Removes invalid characters from names to make them safe for filenames."""
    if not name or name == "N/A":
        return "Unknown_Student"
    # Remove special characters and replace spaces with underscores
    clean_name = re.sub(r'[^\w\s-]', '', name).strip().replace(' ', '_')
    return clean_name

def download_image(url, student_name, scholar_no):
    """Downloads an image and saves it as Name_ScholarNo.jpg"""
    try:
        if not url or url == "N/A":
            return "N/A"
        
        # Clean URL if it's relative
        if not url.startswith('http'):
            url = "https://theedenschool.in/schoolerp/" + url

        img_data = requests.get(url, timeout=10).content
        
        # Create filename: StudentName_ScholarNo.jpg
        safe_name = sanitize_filename(student_name)
        filename = f"{safe_name}_{scholar_no}.jpg"
        filepath = os.path.join(PHOTO_FOLDER, filename)
        
        with open(filepath, 'wb') as f:
            f.write(img_data)
        return filename
    except Exception:
        return "Error"

def scrape_single_id(student_id):
    b64_val = get_b64_id(student_id)
    params = {'stuid': b64_val}
    
    try:
        response = requests.get(BASE_URL, params=params, timeout=10)
        if response.status_code == 200 and "Scholar No" in response.text:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            def get_val(label):
                tag = soup.find('strong', string=lambda x: x and label in x)
                if tag:
                    # Clean up the text: remove label and colon
                    val = tag.get_text(strip=True).split(':')[-1].strip()
                    return val if val else "N/A"
                return "N/A"

            scholar_no = get_val("Scholar No")
            name = get_val("Name")
            class_name = get_val("Class")
            father_name = get_val("Father Name")
            mother_name = get_val("Mother Name")
            
            # Find Image URL
            img_tag = soup.find('img', src=lambda x: x and 'uploads' in x)
            remote_img_url = img_tag['src'] if img_tag else "N/A"
            
            # Download the image locally using the student's name
            local_img_name = "N/A"
            if remote_img_url != "N/A":
                local_img_name = download_image(remote_img_url, name, scholar_no)

            return {
                "System_ID": student_id,
                "Scholar_No": scholar_no,
                "Class": class_name,
                "Student_Name": name,
                "Father_Name": father_name,
                "Mother_Name": mother_name,
                "Image_Filename": local_img_name
            }, student_id
    except Exception:
        pass
    return None, student_id

def main():
    fieldnames = ["System_ID", "Scholar_No", "Class", "Student_Name", "Father_Name", "Mother_Name", "Image_Filename"]
    
    print(f"🚀 Launching Scraper... Target: {START_ID} to {END_ID}")
    
    valid_count = 0
    # Using '\t' (Tab) as separator for the .txt file for better structure
    with open(OUTPUT_FILE, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter='\t')
        writer.writeheader()

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_id = {executor.submit(scrape_single_id, i): i for i in range(START_ID, END_ID + 1)}
            
            for future in as_completed(future_to_id):
                result, s_id = future.result()
                
                if result:
                    writer.writerow(result)
                    valid_count += 1
                    print(f"✅ Saved: {result['Student_Name']} | ID: {s_id}")
                elif s_id % 100 == 0:
                    print(f"📡 Processing... ID {s_id}")

    print(f"\n✨ FINISHED!")
    print(f"📊 Total Records Found: {valid_count}")
    print(f"📂 Data saved to: {OUTPUT_FILE}")
    print(f"🖼️ Photos saved to: {PHOTO_FOLDER}/")

if __name__ == "__main__":
    main()
