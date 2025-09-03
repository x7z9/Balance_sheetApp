#!/usr/bin/env python3
"""
Backend API Testing for Balance Sheet App
Tests all transaction-related endpoints with realistic business data
"""

import requests
import json
from datetime import datetime, date, timedelta
import os
import sys
from pathlib import Path

# Load environment variables
sys.path.append('/app/frontend')
from dotenv import load_dotenv

# Load frontend .env to get backend URL
load_dotenv('/app/frontend/.env')
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL')

if not BACKEND_URL:
    print("❌ REACT_APP_BACKEND_URL not found in frontend/.env")
    sys.exit(1)

BASE_URL = f"{BACKEND_URL}/api"
print(f"🔗 Testing backend at: {BASE_URL}")

class BackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.created_transactions = []
        
    def test_root_endpoint(self):
        """Test the root API endpoint"""
        print("\n📍 Testing root endpoint...")
        try:
            response = self.session.get(f"{BASE_URL}/")
            if response.status_code == 200:
                data = response.json()
                if data.get("message") == "Balance Sheet API":
                    print("✅ Root endpoint working correctly")
                    return True
                else:
                    print(f"❌ Unexpected response: {data}")
                    return False
            else:
                print(f"❌ Root endpoint failed with status {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Root endpoint error: {str(e)}")
            return False
    
    def test_create_transactions(self):
        """Test creating various types of transactions"""
        print("\n💰 Testing transaction creation...")
        
        # Test data with realistic business transactions
        test_transactions = [
            {
                "type": "income",
                "amount": 2500.00,
                "description": "Client payment for web development project",
                "category": "Services",
                "date": "2024-01-15"
            },
            {
                "type": "expense", 
                "amount": 450.00,
                "description": "Office rent payment",
                "category": "Rent",
                "date": "2024-01-01"
            },
            {
                "type": "income",
                "amount": 1800.00,
                "description": "Monthly consulting retainer",
                "category": "Consulting",
                "date": "2024-01-10"
            },
            {
                "type": "expense",
                "amount": 125.50,
                "description": "Software subscriptions and tools",
                "category": "Software",
                "date": "2024-01-05"
            },
            {
                "type": "expense",
                "amount": 89.99,
                "description": "Business internet and phone",
                "category": "Utilities",
                "date": "2024-01-03"
            }
        ]
        
        success_count = 0
        for i, transaction in enumerate(test_transactions):
            try:
                response = self.session.post(
                    f"{BASE_URL}/transactions",
                    json=transaction,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    # Verify response structure
                    required_fields = ['id', 'type', 'amount', 'description', 'date', 'created_at']
                    if all(field in data for field in required_fields):
                        print(f"✅ Transaction {i+1} created: {transaction['type']} ${transaction['amount']}")
                        self.created_transactions.append(data['id'])
                        success_count += 1
                    else:
                        print(f"❌ Transaction {i+1} missing required fields: {data}")
                else:
                    print(f"❌ Transaction {i+1} failed with status {response.status_code}: {response.text}")
            except Exception as e:
                print(f"❌ Transaction {i+1} error: {str(e)}")
        
        print(f"📊 Created {success_count}/{len(test_transactions)} transactions successfully")
        return success_count == len(test_transactions)
    
    def test_get_transactions(self):
        """Test retrieving transactions with various filters"""
        print("\n📋 Testing transaction retrieval...")
        
        # Test getting all transactions
        try:
            response = self.session.get(f"{BASE_URL}/transactions")
            if response.status_code == 200:
                transactions = response.json()
                print(f"✅ Retrieved {len(transactions)} transactions")
                
                # Verify transaction structure
                if transactions:
                    first_tx = transactions[0]
                    required_fields = ['id', 'type', 'amount', 'description', 'date']
                    if all(field in first_tx for field in required_fields):
                        print("✅ Transaction structure is correct")
                    else:
                        print(f"❌ Transaction missing fields: {first_tx}")
                        return False
                
                # Test date filtering
                print("🗓️ Testing date range filtering...")
                start_date = "2024-01-01"
                end_date = "2024-01-31"
                
                response = self.session.get(
                    f"{BASE_URL}/transactions",
                    params={"start_date": start_date, "end_date": end_date}
                )
                
                if response.status_code == 200:
                    filtered_transactions = response.json()
                    print(f"✅ Date filtering works: {len(filtered_transactions)} transactions in range")
                else:
                    print(f"❌ Date filtering failed: {response.status_code}")
                    return False
                
                # Test type filtering
                print("🏷️ Testing type filtering...")
                response = self.session.get(
                    f"{BASE_URL}/transactions",
                    params={"transaction_type": "income"}
                )
                
                if response.status_code == 200:
                    income_transactions = response.json()
                    print(f"✅ Type filtering works: {len(income_transactions)} income transactions")
                    
                    # Verify all returned transactions are income
                    if all(tx['type'] == 'income' for tx in income_transactions):
                        print("✅ Type filter correctly returns only income transactions")
                    else:
                        print("❌ Type filter returned mixed transaction types")
                        return False
                else:
                    print(f"❌ Type filtering failed: {response.status_code}")
                    return False
                
                return True
            else:
                print(f"❌ Get transactions failed with status {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Get transactions error: {str(e)}")
            return False
    
    def test_transaction_summary(self):
        """Test transaction summary calculations"""
        print("\n📊 Testing transaction summary...")
        
        try:
            response = self.session.get(f"{BASE_URL}/transactions/summary")
            if response.status_code == 200:
                summary = response.json()
                required_fields = ['total_income', 'total_expenses', 'net_profit', 'transaction_count']
                
                if all(field in summary for field in required_fields):
                    print("✅ Summary structure is correct")
                    print(f"   💰 Total Income: ${summary['total_income']}")
                    print(f"   💸 Total Expenses: ${summary['total_expenses']}")
                    print(f"   📈 Net Profit: ${summary['net_profit']}")
                    print(f"   🔢 Transaction Count: {summary['transaction_count']}")
                    
                    # Verify calculation logic
                    expected_net = summary['total_income'] - summary['total_expenses']
                    if abs(summary['net_profit'] - expected_net) < 0.01:  # Allow for floating point precision
                        print("✅ Net profit calculation is correct")
                    else:
                        print(f"❌ Net profit calculation error: expected {expected_net}, got {summary['net_profit']}")
                        return False
                    
                    # Test with date filtering
                    print("🗓️ Testing summary with date filtering...")
                    response = self.session.get(
                        f"{BASE_URL}/transactions/summary",
                        params={"start_date": "2024-01-01", "end_date": "2024-01-31"}
                    )
                    
                    if response.status_code == 200:
                        filtered_summary = response.json()
                        print(f"✅ Filtered summary works: {filtered_summary['transaction_count']} transactions")
                    else:
                        print(f"❌ Filtered summary failed: {response.status_code}")
                        return False
                    
                    return True
                else:
                    print(f"❌ Summary missing required fields: {summary}")
                    return False
            else:
                print(f"❌ Summary failed with status {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Summary error: {str(e)}")
            return False
    
    def test_chart_data(self):
        """Test chart data endpoint"""
        print("\n📈 Testing chart data...")
        
        try:
            response = self.session.get(f"{BASE_URL}/transactions/chart-data")
            if response.status_code == 200:
                chart_data = response.json()
                required_fields = ['labels', 'income', 'expenses', 'net_profit']
                
                if all(field in chart_data for field in required_fields):
                    print("✅ Chart data structure is correct")
                    print(f"   📅 Date labels: {len(chart_data['labels'])} days")
                    print(f"   💰 Income data points: {len(chart_data['income'])}")
                    print(f"   💸 Expense data points: {len(chart_data['expenses'])}")
                    print(f"   📊 Net profit data points: {len(chart_data['net_profit'])}")
                    
                    # Verify data consistency
                    data_lengths = [
                        len(chart_data['labels']),
                        len(chart_data['income']),
                        len(chart_data['expenses']),
                        len(chart_data['net_profit'])
                    ]
                    
                    if len(set(data_lengths)) == 1:
                        print("✅ All chart data arrays have consistent length")
                    else:
                        print(f"❌ Chart data arrays have inconsistent lengths: {data_lengths}")
                        return False
                    
                    # Test with date filtering
                    print("🗓️ Testing chart data with date filtering...")
                    response = self.session.get(
                        f"{BASE_URL}/transactions/chart-data",
                        params={"start_date": "2024-01-01", "end_date": "2024-01-31"}
                    )
                    
                    if response.status_code == 200:
                        filtered_chart = response.json()
                        print(f"✅ Filtered chart data works: {len(filtered_chart['labels'])} data points")
                    else:
                        print(f"❌ Filtered chart data failed: {response.status_code}")
                        return False
                    
                    return True
                else:
                    print(f"❌ Chart data missing required fields: {chart_data}")
                    return False
            else:
                print(f"❌ Chart data failed with status {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Chart data error: {str(e)}")
            return False
    
    def test_delete_transactions(self):
        """Test deleting transactions"""
        print("\n🗑️ Testing transaction deletion...")
        
        if not self.created_transactions:
            print("❌ No transactions available for deletion testing")
            return False
        
        # Test deleting a valid transaction
        transaction_id = self.created_transactions[0]
        try:
            response = self.session.delete(f"{BASE_URL}/transactions/{transaction_id}")
            if response.status_code == 200:
                data = response.json()
                if data.get("message") == "Transaction deleted successfully":
                    print(f"✅ Transaction {transaction_id} deleted successfully")
                    
                    # Verify transaction is actually deleted
                    response = self.session.get(f"{BASE_URL}/transactions")
                    if response.status_code == 200:
                        remaining_transactions = response.json()
                        if not any(tx['id'] == transaction_id for tx in remaining_transactions):
                            print("✅ Transaction confirmed deleted from database")
                        else:
                            print("❌ Transaction still exists in database after deletion")
                            return False
                    
                    # Test deleting non-existent transaction
                    print("🔍 Testing deletion of non-existent transaction...")
                    fake_id = "non-existent-id-12345"
                    response = self.session.delete(f"{BASE_URL}/transactions/{fake_id}")
                    if response.status_code == 404:
                        print("✅ Correctly returns 404 for non-existent transaction")
                    else:
                        print(f"❌ Expected 404 for non-existent transaction, got {response.status_code}")
                        return False
                    
                    return True
                else:
                    print(f"❌ Unexpected delete response: {data}")
                    return False
            else:
                print(f"❌ Delete failed with status {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Delete error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting Backend API Tests for Balance Sheet App")
        print("=" * 60)
        
        test_results = {
            "Root Endpoint": self.test_root_endpoint(),
            "Create Transactions": self.test_create_transactions(),
            "Get Transactions": self.test_get_transactions(),
            "Transaction Summary": self.test_transaction_summary(),
            "Chart Data": self.test_chart_data(),
            "Delete Transactions": self.test_delete_transactions()
        }
        
        print("\n" + "=" * 60)
        print("📋 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        passed = 0
        total = len(test_results)
        
        for test_name, result in test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name:<25} {status}")
            if result:
                passed += 1
        
        print(f"\n📊 Overall Result: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All backend tests passed successfully!")
            return True
        else:
            print("⚠️ Some backend tests failed. Check the details above.")
            return False

if __name__ == "__main__":
    tester = BackendTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)