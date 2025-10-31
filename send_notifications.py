
import firebase_admin
from firebase_admin import credentials
from firebase_admin import messaging
from firebase_admin import db
import json
import os
from datetime import datetime

# Initialize Firebase (load from environment variable or file)
try:
    # Option 1: Load from JSON file (if in repo)
    cred = credentials.Certificate('serviceAccount.json')
    firebase_admin.initialize_app(cred)
except FileNotFoundError:
    # Option 2: Load from environment variable (recommended for GitHub Actions)
    service_account_json = os.getenv('FIREBASE_SERVICE_ACCOUNT_JSON')
    if service_account_json:
        cred_dict = json.loads(service_account_json)
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
    else:
        print("Error: Firebase credentials not found!")
        exit(1)

def send_notifications():
    """
    Query Firestore for pending notifications and send them via FCM.
    """
    try:
        db_instance = firebase_admin.get_app().database()

        # Get reference to 'notifications' collection
        notifications_ref = db.reference('notifications')
        notifications = notifications_ref.get()

        if not notifications:
            print(f"[{datetime.now()}] No notifications to send.")
            return

        # Iterate through pending notifications
        for notif_id, notif_data in notifications.items():
            if notif_data.get('sent') == True:
                continue  # Skip already sent

            fcm_token = notif_data.get('fcmToken')
            if not fcm_token:
                print(f"[{datetime.now()}] Skipping notification {notif_id}: No FCM token")
                continue

            # Prepare payload
            title = notif_data.get('title', '🛎 New Order!')
            body = notif_data.get('body', 'New order placed.')

            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data={
                    'orderId': notif_data.get('orderId', ''),
                    'type': notif_data.get('type', ''),
                },
                token=fcm_token,
            )

            # Send message
            response = messaging.send(message)
            print(f"[{datetime.now()}] Successfully sent notification {notif_id}: {response}")

            # Mark as sent
            notifications_ref.child(notif_id).update({'sent': True})

    except Exception as e:
        print(f"[{datetime.now()}] Error sending notifications: {e}")

if __name__ == '__main__':
    print(f"[{datetime.now()}] Starting notification job...")
    send_notifications()
    print(f"[{datetime.now()}] Notification job completed.")
