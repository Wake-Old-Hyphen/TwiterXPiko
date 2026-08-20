import xml.etree.ElementTree as ET
import os
import subprocess
import sys

NEW_PACKAGE_NAME = "com.twitter.androie"
OLD_PACKAGE = "com.twitter.android"
NEW_APP_NAME = "Z²"
ANDROID = "{http://schemas.android.com/apk/res/android}"
ALLOWED_PERMISSIONS = ["android.permission.FOREGROUND_SERVICE", "android.permission.FOREGROUND_SERVICE_DATA_SYNC", "android.permission.INTERNET", "android.permission.ACCESS_NETWORK_STATE", "android.permission.ACCESS_WIFI_STATE"]

def main():
    mode = os.environ.get("MODE", "clone")
    apk_file = os.environ.get("PATCHED_APK_PATH", "twitter-patched.apk")
    if not os.path.exists(apk_file):
        print("Patched APK not found")
        sys.exit(1)

    decoded_dir = "twitter_decoded"
    print("Decoding APK in " + mode + " mode...")
    subprocess.run(["apktool", "d", apk_file, "-o", decoded_dir, "-f"], check=True)

    manifest_path = os.path.join(decoded_dir, "AndroidManifest.xml")
    tree = ET.parse(manifest_path)
    root = tree.getroot()

    if mode == "clone":
        root.set("package", NEW_PACKAGE_NAME)
        root.set(ANDROID + "sharedUserId", NEW_PACKAGE_NAME + ".shared")
        app = root.find("application")
        if app is not None:
            app.set(ANDROID + "label", NEW_APP_NAME)

    removed = 0
    for perm_type in ["uses-permission", "uses-permission-sdk-23"]:
        for perm in list(root.findall(perm_type)):
            perm_name = perm.get(ANDROID + "name")
            if not perm_name:
                continue
            if perm_name in ALLOWED_PERMISSIONS:
                continue
            root.remove(perm)
            removed += 1
    print("Removed " + str(removed) + " requested permissions (only the 5 allowed remain)")

    if mode == "clone":
        renamed = 0
        for perm in list(root.findall("permission")):
            perm_name = perm.get(ANDROID + "name")
            if perm_name and perm_name.startswith(OLD_PACKAGE):
                perm.set(ANDROID + "name", perm_name.replace(OLD_PACKAGE, NEW_PACKAGE_NAME, 1))
                renamed += 1
        for element in root.iter():
            ref = element.get(ANDROID + "permission")
            if ref and ref.startswith(OLD_PACKAGE):
                element.set(ANDROID + "permission", ref.replace(OLD_PACKAGE, NEW_PACKAGE_NAME, 1))
                renamed += 1
        print("Renamed " + str(renamed) + " declared permission entries (prevents install conflict with official X)")

    bad = []
    for perm in list(root.findall("uses-permission")) + list(root.findall("uses-permission-sdk-23")):
        name = perm.get(ANDROID + "name")
        if name and name not in ALLOWED_PERMISSIONS:
            bad.append(name)
    if mode == "clone":
        for perm in root.findall("permission"):
            name = perm.get(ANDROID + "name")
            if name and name.startswith(OLD_PACKAGE):
                bad.append(name)
        for element in root.iter():
            ref = element.get(ANDROID + "permission")
            if ref and ref.startswith(OLD_PACKAGE):
                bad.append(ref)
    if bad:
        print("❌ MANIFEST VERIFICATION FAILED:")
        for b in bad:
            print("   " + b)
        sys.exit(1)
    print("✅ Manifest verification passed")

    tree.write(manifest_path, encoding="utf-8", xml_declaration=True)

    if mode == "clone":
        strings_path = os.path.join(decoded_dir, "res", "values", "strings.xml")
        if os.path.exists(strings_path):
            str_tree = ET.parse(strings_path)
            str_root = str_tree.getroot()
            for string in str_root.findall("string"):
                if string.get("name") in ["app_name", "title", "name"]:
                    string.text = NEW_APP_NAME
            str_tree.write(strings_path, encoding="utf-8", xml_declaration=True)
            print("App name changed to Z²")

    processed_apk = "twitter-processed-unsigned.apk"
    print("Rebuilding APK...")
    subprocess.run(["apktool", "b", decoded_dir, "-o", processed_apk, "--use-aapt2"], check=True)

    track = os.environ.get("TRACK_LABEL", "Unknown")
    apk_version = os.environ.get("APK_VERSION", "unknown")
    patch_version = os.environ.get("PATCH_VERSION", "unknown")
    prefix = "Twitter-Z2-Piko-" if mode == "clone" else "Twitter-Piko-"
    final_apk = prefix + track + "-v" + apk_version + "-" + patch_version + "-arm64-v8a.apk"

    keystore = "debug.keystore"
    if not os.path.exists(keystore):
        print("Generating keystore...")
        subprocess.run(["keytool", "-genkey", "-v", "-keystore", keystore, "-alias", "z2debug", "-keyalg", "RSA", "-keysize", "2048", "-validity", "10000", "-storepass", "android", "-keypass", "android", "-dname", "CN=Z2"], check=True)

    print("Signing APK...")
    subprocess.run(["apksigner", "sign", "--ks", keystore, "--ks-pass", "pass:android", "--out", final_apk, processed_apk], check=True)

    result = subprocess.run(["aapt", "dump", "permissions", final_apk], capture_output=True, text=True)
    bad_final = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if line.startswith("uses-permission:") and "name='" in line:
            name = line.split("name='")[1].split("'")[0]
            if name not in ALLOWED_PERMISSIONS:
                bad_final.append(name)
    if bad_final:
        print("❌ FINAL APK VERIFICATION FAILED:")
        for b in bad_final:
            print("   " + b)
        sys.exit(1)
    print("✅ Final APK permissions verified clean:")
    print(result.stdout)

    print("SUCCESS: " + final_apk)
    subprocess.run(["rm", "-rf", decoded_dir, processed_apk])

if __name__ == "__main__":
    main()        print("Generating keystore...")
        subprocess.run(["keytool", "-genkey", "-v", "-keystore", keystore, "-alias", "z2debug", "-keyalg", "RSA", "-keysize", "2048", "-validity", "10000", "-storepass", "android", "-keypass", "android", "-dname", "CN=Z2"], check=True)

    print("Signing APK...")
    subprocess.run(["apksigner", "sign", "--ks", keystore, "--ks-pass", "pass:android", "--out", final_apk, cloned_apk], check=True)

    # MANDATORY CHECK 2: final signed APK must contain no Twitter permissions
    result = subprocess.run(["aapt", "dump", "permissions", final_apk], capture_output=True, text=True)
    bad_final = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if line.startswith("uses-permission:") and "name='" in line:
            name = line.split("name='")[1].split("'")[0]
            if name not in ALLOWED_PERMISSIONS and not name.startswith(NEW_PACKAGE_NAME):
                bad_final.append(name)
        if line.startswith("permission:") and OLD_PACKAGE in line:
            bad_final.append(line)
    if bad_final:
        print("❌ FINAL APK VERIFICATION FAILED:")
        for b in bad_final:
            print("   " + b)
        sys.exit(1)
    print("✅ Final APK permissions verified clean:")
    print(result.stdout)

    print("SUCCESS: " + final_apk)
    subprocess.run(["rm", "-rf", decoded_dir, cloned_apk])

if __name__ == "__main__":
    main()
