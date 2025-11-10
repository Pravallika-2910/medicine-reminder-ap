import time
import datetime
import json
import os
from plyer import notification

def load_medicines():
    path = "/data/data/org.test.medicinereminder/files/app/medicines.json"
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except:
            return []
    return []

def main():
    print("💊 Background service started")
    last_notified = set()

    while True:
        now = datetime.datetime.now().strftime("%H:%M")
        medicines = load_medicines()

        for med in medicines:
            if med["time"] == now and med["time"] not in last_notified:
                last_notified.add(med["time"])
                try:
                    notification.notify(
                        title="💊 Medicine Reminder",
                        message=f"Time to take {med['name']}",
                        timeout=10
                    )
                    print(f"Notification sent for {med['name']}")
                except Exception as e:
                    print("Notification error:", e)
        time.sleep(30)

if __name__ == "__main__":
    main()

