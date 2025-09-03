from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timezone, date
from enum import Enum

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Transaction Types
class TransactionType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"

# Define Models
class Transaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: TransactionType
    amount: float
    description: str
    category: Optional[str] = None
    date: date
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TransactionCreate(BaseModel):
    type: TransactionType
    amount: float
    description: str
    category: Optional[str] = None
    date: date

class TransactionSummary(BaseModel):
    total_income: float
    total_expenses: float
    net_profit: float
    transaction_count: int

# Helper functions for MongoDB serialization
def prepare_for_mongo(data):
    if isinstance(data.get('date'), date):
        data['date'] = data['date'].isoformat()
    if isinstance(data.get('created_at'), datetime):
        data['created_at'] = data['created_at'].isoformat()
    return data

def parse_from_mongo(item):
    if isinstance(item.get('date'), str):
        item['date'] = datetime.fromisoformat(item['date']).date()
    if isinstance(item.get('created_at'), str):
        item['created_at'] = datetime.fromisoformat(item['created_at'])
    return item

# Routes
@api_router.get("/")
async def root():
    return {"message": "Balance Sheet API"}

@api_router.post("/transactions", response_model=Transaction)
async def create_transaction(transaction: TransactionCreate):
    try:
        # Create transaction object
        transaction_obj = Transaction(**transaction.dict())
        
        # Prepare for MongoDB storage
        transaction_dict = prepare_for_mongo(transaction_obj.dict())
        
        # Insert into database
        result = await db.transactions.insert_one(transaction_dict)
        
        if result.inserted_id:
            return transaction_obj
        else:
            raise HTTPException(status_code=500, detail="Failed to create transaction")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.get("/transactions", response_model=List[Transaction])
async def get_transactions(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    transaction_type: Optional[TransactionType] = None
):
    try:
        # Build query filters
        query = {}
        
        if start_date or end_date:
            date_filter = {}
            if start_date:
                date_filter["$gte"] = start_date
            if end_date:
                date_filter["$lte"] = end_date
            query["date"] = date_filter
        
        if transaction_type:
            query["type"] = transaction_type
        
        # Fetch transactions
        transactions = await db.transactions.find(query).sort("date", -1).to_list(1000)
        
        # Parse from MongoDB and return
        parsed_transactions = [parse_from_mongo(tx) for tx in transactions]
        return [Transaction(**tx) for tx in parsed_transactions]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.get("/transactions/summary", response_model=TransactionSummary)
async def get_transaction_summary(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    try:
        # Build query filters
        query = {}
        
        if start_date or end_date:
            date_filter = {}
            if start_date:
                date_filter["$gte"] = start_date
            if end_date:
                date_filter["$lte"] = end_date
            query["date"] = date_filter
        
        # Fetch all transactions
        transactions = await db.transactions.find(query).to_list(None)
        
        # Calculate summary
        total_income = sum(tx['amount'] for tx in transactions if tx['type'] == 'income')
        total_expenses = sum(tx['amount'] for tx in transactions if tx['type'] == 'expense')
        net_profit = total_income - total_expenses
        transaction_count = len(transactions)
        
        return TransactionSummary(
            total_income=total_income,
            total_expenses=total_expenses,
            net_profit=net_profit,
            transaction_count=transaction_count
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.delete("/transactions/{transaction_id}")
async def delete_transaction(transaction_id: str):
    try:
        result = await db.transactions.delete_one({"id": transaction_id})
        if result.deleted_count:
            return {"message": "Transaction deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Transaction not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.get("/transactions/chart-data")
async def get_chart_data(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    try:
        # Build query filters
        query = {}
        
        if start_date or end_date:
            date_filter = {}
            if start_date:
                date_filter["$gte"] = start_date
            if end_date:
                date_filter["$lte"] = end_date
            query["date"] = date_filter
        
        # Fetch transactions
        transactions = await db.transactions.find(query).sort("date", 1).to_list(None)
        
        # Group by date for line chart
        daily_data = {}
        for tx in transactions:
            tx_date = tx['date']
            if tx_date not in daily_data:
                daily_data[tx_date] = {'income': 0, 'expenses': 0, 'net': 0}
            
            if tx['type'] == 'income':
                daily_data[tx_date]['income'] += tx['amount']
            else:
                daily_data[tx_date]['expenses'] += tx['amount']
            
            daily_data[tx_date]['net'] = daily_data[tx_date]['income'] - daily_data[tx_date]['expenses']
        
        # Format for chart
        chart_data = {
            'labels': list(daily_data.keys()),
            'income': [daily_data[date]['income'] for date in daily_data.keys()],
            'expenses': [daily_data[date]['expenses'] for date in daily_data.keys()],
            'net_profit': [daily_data[date]['net'] for date in daily_data.keys()]
        }
        
        return chart_data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()