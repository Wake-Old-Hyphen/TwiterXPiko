import xml.etree.ElementTree as ET
import os
import subprocess
import sys

# --- CONFIGURATION ---
NEW_PACKAGE_NAME = "com.twitter.androie"
NEW_APP_NAME = "Z²"
ALLOWED_PERMISSIONS = {
    "android.permission.FOREGROUND_SERVICE",
    "android.permission.FOREGROUND_SERVICE_DATA_SYNC",
    "android.permission.INTERNET",
    "android.permission.ACCESS_NETWORK_STATE",
    "android.permission.ACCESS_WIFI_STATE"
}
ANDROID_NS = {'android': 'http://schemas.android.com/apk/res/android'}
ET.register_namespace('android', ANDROID_NS['android'])

def main():
    apk_file = os.environ.get("PATCHED_APK_PATH", "twitter-patched.apk")
    variant = os.environ.get("TRACK", "stable")
    apk_version = os.environ.get("APK_VERSION", "unknown")
    
    if not os.path.exists(apk_file):
        print(f"❌ Patched APK not found at {apk_file}")
        sys.exit(1)

    decoded_dir = "twitter_decoded"
    
    # 1. Decode APK
    print(f"🔓 Decoding {apk_file}...")
    subprocess.run(["apktool", "d", apk_file, "-o", decoded_dir, "-f"], check=True)

    # 2. Modify AndroidManifest.xml
    manifest_path = os.path.join(decoded_dir, "AndroidManifest.xml")
    tree = ET.parse(manifest_path)
    root = tree.getroot()

    # Change Package Name
    root.set("package", NEW_PACKAGE_NAME)
    
    # Change sharedUserId
    shared_user_id_attr = f"{{{ANDROID_NS['android']}}}sharedUserId"
    root.set(shared_user_id_attr, f"{NEW_PACKAGE_NAME}.shared")

    # Change Application Label to Z²
    app = root.find("application")
    if app is not None:
        app.set(f"{{{ANDROID_NS['android']}}}label", NEW_APP_NAME)

    # Strip Unwanted Permissions
    permissions_removed = 0
    for perm_type in ["uses-permission", "uses-permission-sdk-23"]:
        for perm in list(root.findall(perm_type)):
            perm_name = perm.get(f"{{{ANDROID_NS['android']}}}name")
            if perm_name and perm_name not in ALLOWED_PERMISSIONS:
                root.remove(perm)
                permissions_removed += 1

    tree.write(manifest_path, encoding="utf-8", xml_declaration=True)
    print(f"✅ AndroidManifest.xml modified! (Removed {permissions_removed} permissions)")

    # 3. Modify strings.xml (Fallback for App Name)
    strings_path = os.path.join(decoded_dir, "res", "values", "strings.xml")
    if os.path.exists(strings_path):
        str_tree = ET.parse(strings_path)
        str_root = str_tree.getroot()
        for string in str_root.findall("string"):
            if string.get("name") in ["app_name", "title", "name"]:
                string.text = NEW_APP_NAME
        str_tree.write(strings_path, encoding="utf-8", xml_declaration=True)
        print("✅ App name changed to Z² in strings.xml!")

    # 4. Rebuild APK (using aapt2 for modern resource support)
    cloned_apk = "twitter-z2-cloned-unsigned.apk"
    print(f"🔨 Rebuilding APK as {cloned_apk}...")
    subprocess.run(["apktool", "b", decoded_dir, "-o", cloned_apk, "--use-aapt2"], check=True)

    apk_version = os.environ.get("APK_VERSION", "unknown")
    patch_version = os.environ.get("PATCH_VERSION", "unknown")

    # 5. Sign the APK
    keystore = "debug.keystore"
    if not os.path.exists(keystore):
        subprocess.run([
            "keytool", "-genkey", "-v", "-keystore", keystore,
            "-alias", "z2debug", "-keyalg", "RSA", "-keysize", "2048",
            "-validity", "10000", "-storepass", "android", "-keypass", "android",
            "-dname", "CN=Z2, OU=Z2, O=Z2, L=Z2, S=Z2, C=Z2"
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Apply the new naming convention: Twitter-Z2-Piko-v{app_version}-{patch_version}-arm64-v8a.apk
    final_apk = f"Twitter-Z2-Piko-v{apk_version}-{patch_version}-arm64-v8a.apk"
    
    print(f"🖋️ Signing Cloned APK as {final_apk}...")
    subprocess.run([
        "apksigner", "sign", "--ks", keystore, "--ks-pass", "pass:android",
        "--out", final_apk, cloned_apk
    ], check=True)

    print(f"🎉 SUCCESS! Cloned APK ready: {final_apk}")

    # Morphe-style naming: Twitter-Z2-Piko-{version}-arm64-v8a.apk
    final_apk = f"Twitter-Z2-Piko-{apk_version}-arm64-v8a.apk"
    print(f"🖋️ Signing APK as {final_apk}...")
    subprocess.run([
        "apksigner", "sign", "--ks", keystore, "--ks-pass", "pass:android",
        "--out", final_apk, cloned_apk
    ], check=True)

    print(f"🎉 SUCCESS! Cloned APK ready: {final_apk}")
    
    # Clean up temporary files
    subprocess.run(["rm", "-rf", decoded_dir, cloned_apk])

if __name__ == "__main__":
    main()
