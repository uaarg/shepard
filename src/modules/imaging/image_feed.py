import shutil
import time

SOURCE_IMAGE = "live_feed_test.jpeg"

while True:
    try:

        shutil.copy(SOURCE_IMAGE, "latest.jpg")

        time.sleep(2)

    except Exception as e:
        print(f"Error: {e}")
        break