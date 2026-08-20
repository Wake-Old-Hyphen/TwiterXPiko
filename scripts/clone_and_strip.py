import xml.etree.ElementTree as ET
import os
import subprocess
import sys

NEW_PACKAGE_NAME = "com.twitter.androie"
NEW_APP_NAME = "Z²"
ALLOWED_PERMISSIONS = ["android.permission.FOREGROUND_SERVICE", "android.permission.FOREGROUND_SERVICE_DATA_SYNC", "android.permission.INTERNET", "android.permission.ACCESS_NETWORK_STATE", "android.permission.ACCESS_WIFI_STATE"]

def main():
    apk_file = os.environ.get("PATCHED_APK_PATH", "twitter-patched-clone.apk")
    if not os.path.exists(apk_file):
        sys.exit(1)

    decoded_dir = "twitter_decoded"
    subprocess.run(["apktool", "d", apk_file, "-o", decoded_dir, "-f", "--use-aapt2"], check=True)

    manifest_path = os.path.join(decoded_dir, "AndroidManifest.xml")
    tree = ET.parse(manifest_path)
    root = tree.getroot()

    root.set("package", NEW_PACKAGE_NAME)
    root.set("{http://schemas.android.com/apk/res/android}sharedUserId", NEW_PACKAGE_NAME + ".shared")

    app = root.find("application")
    if app is not None:
        app.set("{http://schemas.android.com/apk/res/android}label", NEW_APP_NAME)

    for perm_type in ["uses-permission", "uses-permission-sdk-23"]:
        for perm in list(root.findall(perm_type)):
            perm_name = perm.get("{http://schemas.android.com/apk/res/android}name")
            if perm_name and perm_name not in ALLOWED_PERMISSIONS:
                root.remove(perm)

    tree.write(manifest_path, encoding="utf-8", xml_declaration=True)

    strings_path = os.path.join(decoded_dir, "res", "values", "strings.xml")
    if os.path.exists(strings_path):
        str_tree = ET.parse(strings_path)
        str_root = str_tree.getroot()
        for string in str_root.findall("string"):
            if string.get("name") in ["app_name", "title", "name"]:
                string.text = NEW_APP_NAME
        str_tree.write(strings_path, encoding="utf-8", xml_declaration=True)

    cloned_apk = "twitter-z2-cloned-unsigned.apk"
    subprocess.run(["apktool", "b", decoded_dir, "-o", cloned_apk, "--use-aapt2"], check=True)

    apk_version = os.environ.get("APK_VERSION", "unknown")
    patch_version = os.environ.get("PATCH_VERSION", "unknown")
    final_apk = "Twitter-Z2-Piko-v" + apk_version + "-" + patch_version + "-arm64-v8a.apk"
    
    keystore = "debug.keystore"
    if not os.path.exists(keystore):
        subprocess.run(["keytool", "-genkey", "-v", "-keystore", keystore, "-alias", "z2debug", "-keyalg", "RSA", "-keysize", "2048", "-validity", "10000", "-storepass", "android", "-keypass", "android", "-dname", "CN=Z2"], check=True)

    subprocess.run(["apksigner", "sign", "--ks", keystore, "--ks-pass", "pass:android", "--out", final_apk, cloned_apk], check=True)
    subprocess.run(["rm", "-rf", decoded_dir, cloned_apk])

if __name__ == "__main__":
    main()
