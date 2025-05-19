from fastapi import FastAPI, HTTPException, status
import uvicorn
from pydantic import BaseModel
from pydantic.v1 import validator
from typing import List

app = FastAPI()

ordersList = {} # orders are empty initialy
order_count = 1

class Item(BaseModel):
    name: str
    price: float

    @validator('price')
    def price_must_be_positive(cls, value):
        if value <= 0:
            raise ValueError('Price must be a positive number')
        return value

class OrderCreate(BaseModel):
    customer_name: str
    items: List[Item]

    @validator('customer_name')
    def customer_name_non_empty(cls, value):
        if not value.strip():
            raise ValueError('Customer name cannot be empty')
        return value

    @validator('items')
    def items_non_empty(cls, value):
        if len(value) < 1:
            raise ValueError('Order must contain at least one item')
        return value

class Order(OrderCreate):
    id: int
    status: str
    total: float

class StatusUpdate(BaseModel):
    status: str

@app.get("/orders", response_model=List[Order])
def get_all_orders():
    return list(ordersList.values())

@app.post("/orders", response_model=Order, status_code=status.HTTP_201_CREATED)
def create_order(order_data: OrderCreate):
    global order_count
    total = sum(item.price for item in order_data.items)
    newOrder = Order(
        id=order_count,
        customer_name=order_data.customer_name,
        items=order_data.items,
        status="pending",
        total=total
    )
    ordersList[order_count] = newOrder
    order_count += 1
    return newOrder


@app.get("/orders/{order_id}", response_model=Order)
def get_order(order_id: int):
    if order_id not in ordersList:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return ordersList[order_id]

@app.patch("/orders/{order_id}", response_model=Order)
def update_order_status(order_id: int, status_data: StatusUpdate):
    allowed_statuses = ["pending", "in_progress", "completed", "cancelled"]
    new_status = status_data.status

    if new_status not in allowed_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Allowed values: {allowed_statuses}"
        )
    
    if order_id not in ordersList:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    
    order = ordersList[order_id]
    order.status = new_status
    return order



@app.get("/orders/summary")
def get_summary():
    total_orders = len(ordersList)
    total_value = sum(order.total for order in ordersList.values())
    return {
        "total_orders": total_orders,
        "total_value": total_value
    }




if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)