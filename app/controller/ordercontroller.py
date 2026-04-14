from fastapi import HTTPException
from app.services import DBConn
from datetime import datetime
from app.config.Config import settings
import uuid
import logging

log = logging.getLogger("asyncio")


class OrderController:
    def __init__(self, email: str):
        self.email = email
        self.order_col = settings.order_col
        self.order_history_col = settings.order_history_col

    def add_order(self, order_data):
        """
        Add a new order to the user's order history
        
        Args:
            order_data: AddOrderRequest object containing date, status, detail, and shippingAddress (required)
            
        Returns:
            dict: Success message
            
        Raises:
            HTTPException: If order creation fails or shipping address is missing
        """
        log.info(f"OrderController: Adding order for {self.email}")
        
        # Validate that shipping address is provided
        if not order_data.shippingAddress:
            log.error(f"Order creation failed for {self.email}: Missing shipping address")
            raise HTTPException(status_code=400, detail="Shipping address is required")
        
        # Ensure status defaults to "preparing" if not provided
        order_status = order_data.status if order_data.status else "preparing"
        log.info(f"Adding order with status: {order_status}")
        
        try:
            # Check if user already has an order history document
            existing_record = DBConn.aggregate(
                collection=self.order_history_col,
                match_query={"email": self.email},
                project_fields=["email", "orders"]
            )
            
            # Generate unique order ID (timestamp + uuid)
            timestamp = int(datetime.now().timestamp() * 1000)  # milliseconds
            unique_id = str(uuid.uuid4())[:8]  # first 8 characters of uuid
            order_id = f"{timestamp}-{unique_id}"
            
            # Create new order entry - use the validated status
            new_order = {
                "orderId": order_id,
                "date": order_data.date,
                "status": order_status,
                "detail": [order_detail.dict() for order_detail in order_data.detail],
                "shippingAddress": order_data.shippingAddress.dict()
            }
            
            if existing_record:
                # Update existing document - add new order to orders array
                current_orders = existing_record.get("orders", [])
                current_orders.append(new_order)
                
                DBConn.upsert_doc(
                    collection=self.order_history_col,
                    match_query={"email": self.email},
                    update_data={
                        "orders": current_orders,
                        "updated_at": datetime.now()
                    }
                )
            else:
                # Create new document
                order_history_data = {
                    "email": self.email,
                    "orders": [new_order],
                    "created_at": datetime.now(),
                    "updated_at": datetime.now()
                }
                DBConn.insert_doc(
                    collection=self.order_history_col,
                    payload=order_history_data
                )
            
            # Also store order as individual document in Order collection
            order_document = {
                "email": self.email,
                "orderId": order_id,
                "date": order_data.date,
                "status": order_status,
                "detail": [order_detail.dict() for order_detail in order_data.detail],
                "shippingAddress": order_data.shippingAddress.dict(),
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
            
            DBConn.insert_doc(
                collection=self.order_col,
                payload=order_document
            )
            
            log.info(f"Order {order_id} added successfully for {self.email} (saved to both OrderHistory and Order collections)")
            return {"success": True, "message": "Order added successfully", "orderId": order_id}
            
        except Exception as e:
            log.error(f"Error adding order for {self.email}: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to add order")

    def get_order_history(self):
        """
        Retrieve all orders for the user
        
        Returns:
            dict: Dictionary containing orders array
            
        Raises:
            HTTPException: If retrieval fails
        """
        log.info(f"OrderController: Getting order history for {self.email}")
        
        try:
            # Get order history from OrderHistory collection
            order_record = DBConn.aggregate(
                collection=self.order_history_col,
                match_query={"email": self.email},
                project_fields=["email", "orders"]
            )
            
            if not order_record:
                log.info(f"No order history found for {self.email}")
                return {"orders": []}
            
            orders = order_record.get("orders", [])
            
            # Log the number of orders and confirm status fields are included
            log.info(f"Retrieved {len(orders)} orders for {self.email}")
            for i, order in enumerate(orders):
                log.info(f"Order {i+1}: date={order.get('date')}, status={order.get('status', 'no status')}")
            
            return {"orders": orders}
            
        except Exception as e:
            log.error(f"Error getting order history for {self.email}: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to get order history")

