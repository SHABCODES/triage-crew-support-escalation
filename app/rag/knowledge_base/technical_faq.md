<!-- SYNTHETIC POLICY DOCUMENT -->
# Technical FAQ & Troubleshooting

## 500 Internal Server Errors
If the API returns a 500 error, it typically means a temporary issue on our end. Please check our status page. If the issue persists for more than 10 minutes, contact support with the specific endpoint and timestamp of the failure.

## Webhooks
Webhooks are delivered immediately upon events. If your endpoint is unreachable or returns a non-200 status, we will retry with exponential backoff up to 10 times over 3 days. If you notice delayed webhooks globally, it may be due to high system load.

## Mobile App Crashes
If the mobile app crashes on startup, especially after an OS update (e.g., iOS 15+ or Android 14), please ensure you are running the latest version from the App Store or Google Play. Reinstalling the app often clears corrupted local cache.

## API Key Reset
To reset your API key, go to the Developer Dashboard -> API Keys -> Rotate Key. **Warning:** This immediately invalidates your old key and any integrations using it will break until updated.

## CORS Errors
If you experience CORS (Cross-Origin Resource Sharing) errors when calling our API directly from a browser (e.g., React or Vue apps), this is expected. For security reasons, our main API does not support CORS. You must route requests through your own backend server.
