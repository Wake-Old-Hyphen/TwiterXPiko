import requests
import re
import sys
import os
from bs4 import BeautifulSoup

# APKMirror URLs for different Twitter versions
APKMIRROR_BASE = "https://www.apkmirror.com"
TWITTER_APK_URLS = {
    "latest": f"{APKMIRROR_BASE}/apk/twitter-inc/twitter/",
    "12.2.1": f"{APKMIRROR_BASE}/apk/twitter-inc/twitter/twitter-12-2-1-release/"
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def get_download_url(variant):
    """Get the arm64-v8a APK download URL from APKMirror"""
    if variant == "12.2.1":
        page_url = APKMIRROR_BASE + "/apk/twitter-inc/twitter/twitter-12-2-1-release/twitter-12-2-1-release-2-android-apk-download/"
    else:
        # For latest/recommended, scrape the main page
        response = requests.get(APKMIRROR_BASE + "/apk/twitter-inc/twitter/", headers=HEADERS)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the recommended/latest version link
        version_link = soup.find("a", class_="accent_color")
        if not version_link:
            raise Exception("Could not find Twitter APK on APKMirror")
        
        page_url = APKMIRROR_BASE + version_link['href']
    
    # Now get the actual download link for arm64-v8a
    response = requests.get(page_url, headers=HEADERS)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find arm64-v8a variant
    variants = soup.find_all("div", class_="table-row headerFont")
    for variant_div in variants:
        if "arm64-v8a" in variant_div.text and "nodpi" in variant_div.text:
            download_link = variant_div.find("a", class_="accent_color")
            if download_link:
                return APKMIRROR_BASE + download_link['href']
    
    raise Exception("Could not find arm64-v8a variant on APKMirror")

def download_apk(url, output_path):
    """Download APK from URL"""
    print(f"📥 Downloading APK from: {url}")
    response = requests.get(url, headers=HEADERS, stream=True)
    response.raise_for_status()
    
    with open(output_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    
    print(f"✅ Downloaded to: {output_path}")

def main():
    variant = os.environ.get("APK_VARIANT", "latest")
    output_file = os.environ.get("OUTPUT_APK", "base-twitter.apk")
    
    print(f"🎯 Build variant: {variant}")
    
    try:
        download_url = get_download_url(variant)
        download_apk(download_url, output_file)
    except Exception as e:
        print(f"❌ Error downloading APK: {e}")
        print("\n💡 If APKMirror is blocking downloads, you can:")
        print("   1. Manually download the APK and upload it to the repository")
        print("   2. Use a different APK source")
        sys.exit(1)

if __name__ == "__main__":
    main()
