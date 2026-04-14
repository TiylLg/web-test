from fastapi import HTTPException
from fastapi.responses import Response
from app.services import DBConn
from app.config.Config import settings
import csv
import io
import logging

log = logging.getLogger("asyncio")


class DropshipController:
    def __init__(self):
        self.order_col = settings.order_col

    def export_orders_for_date(self, date: str):
        """
        Export all orders for a specific date in CSV format for dropship distributor.
        
        Args:
            date: Date in YYYY-MM-DD format
            
        Returns:
            Response: CSV file response with proper headers for download
            
        Raises:
            HTTPException: If no orders found or export fails
        """
        log.info(f"DropshipController: Exporting orders for date: {date}")
        
        try:
            # Query all orders for the specified date from Order collection
            orders = DBConn.find_docs(
                collection=self.order_col,
                query={"date": date}
            )
            
            if not orders:
                log.info(f"No orders found for date: {date}")
                raise HTTPException(status_code=404, detail=f"No orders found for date {date}")
            
            log.info(f"Found {len(orders)} orders for date: {date}")
            
            # Create CSV in memory using StringIO
            csv_buffer = io.StringIO()
            csv_writer = csv.writer(csv_buffer)
            
            # Write header
            csv_writer.writerow([
                'Order ID',
                'Date',
                'Product Name',
                'Quantity',
                'Ship To Name',
                'Address Line 1',
                'Address Line 2',
                'City',
                'State',
                'Zip Code',
                'Country',
                'Phone'
            ])
            
            # Write order data
            for order in orders:
                order_id = order.get('orderId', 'N/A')
                order_date = order.get('date', 'N/A')
                details = order.get('detail', [])
                shipping = order.get('shippingAddress', {})
                
                # Extract shipping address fields
                ship_name = shipping.get('fullName', 'N/A')
                address_1 = shipping.get('addressLine1', 'N/A')
                address_2 = shipping.get('addressLine2', '')
                city = shipping.get('city', 'N/A')
                state = shipping.get('state', 'N/A')
                zip_code = shipping.get('zipCode', 'N/A')
                country = shipping.get('country', 'N/A')
                phone = shipping.get('phone', 'N/A')
                
                # Write one row per product in the order
                for item in details:
                    product_name = item.get('productName', 'N/A')
                    quantity = item.get('quantity', 0)
                    
                    csv_writer.writerow([
                        order_id,
                        order_date,
                        product_name,
                        quantity,
                        ship_name,
                        address_1,
                        address_2,
                        city,
                        state,
                        zip_code,
                        country,
                        phone
                    ])
            
            # Get CSV content as string
            csv_content = csv_buffer.getvalue()
            csv_buffer.close()
            
            filename = f"dropship_orders_{date}.csv"
            
            log.info(f"Successfully created export file: {filename} with {len(orders)} orders")
            
            # Return Response with CSV content
            return Response(
                content=csv_content,
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}"
                }
            )
            
        except HTTPException:
            raise
        except Exception as e:
            log.error(f"Error exporting orders for date {date}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to export orders: {str(e)}")

