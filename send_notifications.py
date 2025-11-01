import firebase_admin
from firebase_admin import credentials
from firebase_admin import messaging
from firebase_admin import firestore
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
        db_instance = firestore.client()
        notifications_ref = db_instance.collection('notifications')
        notifications = notifications_ref.where('sent', '==', False).stream()

        found_any = False
        for notif in notifications:
            found_any = True
            notif_id = notif.id
            notif_data = notif.to_dict()

            fcm_token = notif_data.get('fcmToken')
            if not fcm_token:
                print(f"[{datetime.now()}] Skipping notification {notif_id}: No FCM token")
                continue

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

            response = messaging.send(message)
            print(f"[{datetime.now()}] Successfully sent notification {notif_id}: {response}")

            # Mark as sent
            notifications_ref.document(notif_id).update({'sent': True})

        if not found_any:
            print(f"[{datetime.now()}] No notifications to send.")

    except Exception as e:
        print(f"[{datetime.now()}] Error sending notifications: {e}")

if __name__ == '__main__':
    print(f"[{datetime.now()}] Starting notification job...")
    send_notifications()
    print(f"[{datetime.now()}] Notification job completed.")
