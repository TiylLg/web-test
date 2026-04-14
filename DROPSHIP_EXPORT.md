# Dropship Order Export Endpoint

This endpoint allows you to export orders for a specific date in CSV format for dropship processing. The CSV file is downloadable directly from the Swagger UI or any HTTP client.

## Architecture

- **Controller**: `DropshipController` handles all business logic
- **Router**: `/api/v1/export-orders` endpoint validates authentication
- **Response**: Direct CSV file download (not streaming)

## Authentication

Unlike other endpoints, this uses **password authentication** instead of JWT tokens.

The password **must** be set in your `.env` file (no default value):
```
DROPSHIP_PASSWORD=your_secure_password_here
```

## Endpoint Details

- **URL**: `/api/v1/export-orders`
- **Method**: `GET`
- **Authentication**: Password in header `X-Dropship-Password`

## Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| date | string | query | Yes | Date in YYYY-MM-DD format |
| X-Dropship-Password | string | header | Yes | Password for authentication |

## Response

- **Success (200)**: CSV file download
- **Unauthorized (401)**: Invalid password
- **Not Found (404)**: No orders found for the specified date
- **Server Error (500)**: Internal error

## CSV Format

The exported CSV file contains the following columns:

| Column | Description |
|--------|-------------|
| Order ID | Unique order identifier |
| Date | Order date |
| Product Name | Product name |
| Quantity | Product quantity |
| Ship To Name | Recipient's full name |
| Address Line 1 | Street address |
| Address Line 2 | Apartment, suite, etc. (optional) |
| City | City |
| State | State/Province |
| Zip Code | Postal code |
| Country | Country |
| Phone | Contact phone number |

**Note**: If an order contains multiple products, there will be one row per product with the same Order ID and shipping information. Email and price information are not included for privacy and business reasons.

## Usage Examples

### cURL

```bash
curl -X GET "http://localhost:8000/api/v1/export-orders?date=2025-10-25" \
  -H "X-Dropship-Password: your_secure_password_here" \
  --output orders.csv
```

### Python (requests)

```python
import requests

url = "http://localhost:8000/api/v1/export-orders"
params = {"date": "2025-10-25"}
headers = {"X-Dropship-Password": "your_secure_password_here"}

response = requests.get(url, params=params, headers=headers)

if response.status_code == 200:
    with open("orders.csv", "wb") as f:
        f.write(response.content)
    print("Orders exported successfully!")
else:
    print(f"Error: {response.status_code} - {response.text}")
```

### JavaScript (fetch)

```javascript
const date = "2025-10-25";
const password = "your_secure_password_here";

fetch(`http://localhost:8000/api/v1/export-orders?date=${date}`, {
  headers: {
    "X-Dropship-Password": password
  }
})
  .then(response => {
    if (response.ok) {
      return response.blob();
    }
    throw new Error(`HTTP error! status: ${response.status}`);
  })
  .then(blob => {
    // Create download link
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `dropship_orders_${date}.csv`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
  })
  .catch(error => console.error("Error:", error));
```

### Swagger UI

1. Navigate to `http://localhost:8000/docs`
2. Find the `/api/v1/export-orders` endpoint
3. Click "Try it out"
4. Enter parameters:
   - `date`: `2025-10-25`
   - `X-Dropship-Password`: `your_secure_password_here`
5. Click "Execute"
6. Click the "Download" button in the response section

### Postman

1. Method: `GET`
2. URL: `http://localhost:8000/api/v1/export-orders`
3. Params:
   - Key: `date`
   - Value: `2025-10-25`
4. Headers:
   - Key: `X-Dropship-Password`
   - Value: `your_secure_password_here`
5. Click "Send"
6. Click "Save Response" to download the CSV file

## Security Considerations

1. **Keep the password secure**: Store it safely and don't commit it to version control
2. **Use HTTPS in production**: Always use HTTPS to encrypt the password in transit
3. **Rotate passwords regularly**: Change the password periodically
4. **Monitor access**: Log all attempts to access this endpoint
5. **IP whitelisting**: Consider adding IP restrictions in production

## Sample CSV Output

```csv
Order ID,Date,Product Name,Quantity,Ship To Name,Address Line 1,Address Line 2,City,State,Zip Code,Country,Phone
1729876543210-abc12345,2025-10-25,Product A,2,John Doe,123 Main St,Apt 4B,New York,NY,10001,United States,555-1234
1729876543210-abc12345,2025-10-25,Product B,1,John Doe,123 Main St,Apt 4B,New York,NY,10001,United States,555-1234
1729876555555-def67890,2025-10-25,Product C,3,Jane Smith,456 Oak Ave,,Los Angeles,CA,90001,United States,555-5678
```

## Troubleshooting

### "Invalid password" error
- Verify the password in your `.env` file matches what you're sending
- Check that there are no extra spaces or newlines in the password
- Ensure the header name is exactly `X-Dropship-Password` (case-sensitive)

### "No orders found for date" error
- Verify the date format is `YYYY-MM-DD`
- Check that orders exist in the database for that date
- Date must match exactly (including timezone considerations)

### File download issues
- Ensure your client properly handles file streaming/downloads
- Check file permissions if saving fails
- Verify sufficient disk space

