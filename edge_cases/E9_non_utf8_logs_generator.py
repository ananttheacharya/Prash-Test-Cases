import zipfile
import os

# [E9] Non-UTF-8 log files in ZIP
# GitHub sometimes outputs raw binary or non-utf8 characters in CI logs (e.g., from certain test runners).
# log_fetcher.py must be able to decode them without crashing.

zip_path = "E9_non_utf8_logs.zip"

print(f"=== [E9] Generating {zip_path} ===")

# Create a zip file containing a text file with invalid UTF-8 bytes
with zipfile.ZipFile(zip_path, 'w') as zf:
    # 0xFF is an invalid byte in UTF-8
    bad_content = b"This is a normal log line.\nHere is some bad data: \xff\xfe\x00\x00\nEnd of log."
    zf.writestr("1_build.txt", bad_content)

print("Created ZIP file. If you run this through log_fetcher.py:")
print("It uses `.decode('utf-8', errors='replace')`")
print("So it will replace the bad bytes with  and succeed without crashing.")
print("Risk: Low - Properly handled.")
