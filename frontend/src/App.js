import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";
import { format } from "date-fns";
import jsPDF from 'jspdf';
import 'jspdf-autotable';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Pagination Component
const Pagination = ({ currentPage, totalPages, onPageChange }) => {
  const getPageNumbers = () => {
    const pages = [];
    const maxVisiblePages = 5;
    
    if (totalPages <= maxVisiblePages) {
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i);
      }
    } else {
      if (currentPage <= 3) {
        pages.push(1, 2, 3, 4, '...', totalPages);
      } else if (currentPage >= totalPages - 2) {
        pages.push(1, '...', totalPages - 3, totalPages - 2, totalPages - 1, totalPages);
      } else {
        pages.push(1, '...', currentPage - 1, currentPage, currentPage + 1, '...', totalPages);
      }
    }
    
    return pages;
  };

  if (totalPages <= 1) return null;

  return (
    <div className="flex items-center justify-center space-x-2 mt-6">
      <button
        onClick={() => onPageChange(currentPage - 1)}
        disabled={currentPage === 1}
        className="px-3 py-2 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        Previous
      </button>
      
      {getPageNumbers().map((page, index) => (
        <button
          key={index}
          onClick={() => typeof page === 'number' ? onPageChange(page) : null}
          disabled={page === '...'}
          className={`px-3 py-2 rounded-lg border ${
            page === currentPage
              ? 'bg-blue-600 text-white border-blue-600'
              : page === '...'
              ? 'border-gray-300 text-gray-400 cursor-default'
              : 'border-gray-300 text-gray-700 hover:bg-gray-50'
          }`}
        >
          {page}
        </button>
      ))}
      
      <button
        onClick={() => onPageChange(currentPage + 1)}
        disabled={currentPage === totalPages}
        className="px-3 py-2 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        Next
      </button>
    </div>
  );
};

// PDF Download Component
const PDFDownload = ({ transactions, summary, startDate, endDate }) => {
  const generatePDF = () => {
    const doc = new jsPDF();
    
    // Header
    doc.setFontSize(20);
    doc.setTextColor(40);
    doc.text('Business Balance Sheet Report', 20, 25);
    
    // Date range
    doc.setFontSize(12);
    doc.setTextColor(100);
    const dateRange = startDate && endDate 
      ? `Period: ${startDate} to ${endDate}`
      : startDate 
      ? `From: ${startDate}`
      : endDate 
      ? `Until: ${endDate}`
      : `All Transactions (Generated: ${format(new Date(), 'yyyy-MM-dd')})`;
    doc.text(dateRange, 20, 35);
    
    // Summary Section
    doc.setFontSize(14);
    doc.setTextColor(40);
    doc.text('Financial Summary', 20, 50);
    
    doc.setFontSize(10);
    doc.setTextColor(100);
    const summaryData = [
      ['Total Income', `$${summary.total_income?.toFixed(2) || '0.00'}`],
      ['Total Expenses', `$${summary.total_expenses?.toFixed(2) || '0.00'}`],
      ['Net Profit/Loss', `$${summary.net_profit?.toFixed(2) || '0.00'}`],
      ['Total Transactions', `${summary.transaction_count || 0}`]
    ];
    
    doc.autoTable({
      startY: 55,
      head: [['Metric', 'Amount']],
      body: summaryData,
      theme: 'grid',
      headStyles: { fillColor: [59, 130, 246] },
      styles: { fontSize: 10 },
      margin: { left: 20, right: 20 }
    });
    
    // Transactions Table
    if (transactions.length > 0) {
      doc.setFontSize(14);
      doc.setTextColor(40);
      doc.text('Transaction Details', 20, doc.lastAutoTable.finalY + 20);
      
      const transactionData = transactions.map(tx => [
        tx.date,
        tx.type === 'income' ? 'Income' : 'Expense',
        tx.description,
        tx.category || 'N/A',
        tx.type === 'income' ? `+$${tx.amount.toFixed(2)}` : `-$${tx.amount.toFixed(2)}`
      ]);
      
      doc.autoTable({
        startY: doc.lastAutoTable.finalY + 25,
        head: [['Date', 'Type', 'Description', 'Category', 'Amount']],
        body: transactionData,
        theme: 'striped',
        headStyles: { fillColor: [59, 130, 246] },
        styles: { fontSize: 9 },
        columnStyles: {
          0: { cellWidth: 25 },
          1: { cellWidth: 20 },
          2: { cellWidth: 60 },
          3: { cellWidth: 25 },
          4: { cellWidth: 30, halign: 'right' }
        },
        margin: { left: 20, right: 20 }
      });
    }
    
    // Footer
    const pageCount = doc.internal.getNumberOfPages();
    for (let i = 1; i <= pageCount; i++) {
      doc.setPage(i);
      doc.setFontSize(8);
      doc.setTextColor(150);
      doc.text(
        `Page ${i} of ${pageCount} | Generated on ${format(new Date(), 'yyyy-MM-dd HH:mm')}`,
        20,
        doc.internal.pageSize.height - 10
      );
    }
    
    // Save the PDF
    const fileName = `balance-sheet-${startDate || 'all'}-${endDate || format(new Date(), 'yyyy-MM-dd')}.pdf`;
    doc.save(fileName);
  };

  return (
    <button
      onClick={generatePDF}
      className="flex items-center gap-2 bg-green-600 text-white py-2 px-4 rounded-lg font-semibold hover:bg-green-700 transition-colors"
    >
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
      Download PDF
    </button>
  );
};
const TransactionForm = ({ onTransactionAdded }) => {
  const [formData, setFormData] = useState({
    type: 'income',
    amount: '',
    description: '',
    category: '',
    date: format(new Date(), 'yyyy-MM-dd')
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    
    try {
      const submitData = {
        ...formData,
        amount: parseFloat(formData.amount)
      };
      
      await axios.post(`${API}/transactions`, submitData);
      
      // Reset form
      setFormData({
        type: 'income',
        amount: '',
        description: '',
        category: '',
        date: format(new Date(), 'yyyy-MM-dd')
      });
      
      onTransactionAdded();
    } catch (error) {
      console.error('Error adding transaction:', error);
      alert('Error adding transaction. Please try again.');
    }
    
    setIsSubmitting(false);
  };

  const setTransactionType = (type) => {
    setFormData({ ...formData, type });
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
      <h2 className="text-2xl font-bold mb-4 text-gray-800">Add Transaction</h2>
      
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Transaction Type Buttons */}
        <div className="flex gap-2 mb-4">
          <button
            type="button"
            onClick={() => setTransactionType('income')}
            className={`flex-1 py-3 px-4 rounded-lg font-semibold transition-colors ${
              formData.type === 'income'
                ? 'bg-green-500 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            + Income/Profit
          </button>
          <button
            type="button"
            onClick={() => setTransactionType('expense')}
            className={`flex-1 py-3 px-4 rounded-lg font-semibold transition-colors ${
              formData.type === 'expense'
                ? 'bg-red-500 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            - Expenses/Spending
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Amount
            </label>
            <input
              type="number"
              step="0.01"
              value={formData.amount}
              onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Enter amount"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Date
            </label>
            <input
              type="date"
              value={formData.date}
              onChange={(e) => setFormData({ ...formData, date: e.target.value })}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Description
          </label>
          <input
            type="text"
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="Enter description"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Category (Optional)
          </label>
          <input
            type="text"
            value={formData.category}
            onChange={(e) => setFormData({ ...formData, category: e.target.value })}
            className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="Enter category"
          />
        </div>

        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg font-semibold hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isSubmitting ? 'Adding...' : 'Add Transaction'}
        </button>
      </form>
    </div>
  );
};

// Summary Cards Component
const SummaryCards = ({ summary }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
      <div className="bg-green-100 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-green-800">Total Income</h3>
        <p className="text-2xl font-bold text-green-600">
          ${summary.total_income?.toFixed(2) || '0.00'}
        </p>
      </div>
      
      <div className="bg-red-100 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-red-800">Total Expenses</h3>
        <p className="text-2xl font-bold text-red-600">
          ${summary.total_expenses?.toFixed(2) || '0.00'}
        </p>
      </div>
      
      <div className={`rounded-lg p-6 ${
        (summary.net_profit || 0) >= 0 ? 'bg-blue-100' : 'bg-orange-100'
      }`}>
        <h3 className={`text-lg font-semibold ${
          (summary.net_profit || 0) >= 0 ? 'text-blue-800' : 'text-orange-800'
        }`}>
          Net Profit/Loss
        </h3>
        <p className={`text-2xl font-bold ${
          (summary.net_profit || 0) >= 0 ? 'text-blue-600' : 'text-orange-600'
        }`}>
          ${summary.net_profit?.toFixed(2) || '0.00'}
        </p>
      </div>
      
      <div className="bg-gray-100 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-800">Total Transactions</h3>
        <p className="text-2xl font-bold text-gray-600">
          {summary.transaction_count || 0}
        </p>
      </div>
    </div>
  );
};

// Transaction List Component
const TransactionList = ({ transactions, onDelete }) => {
  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
      <h2 className="text-2xl font-bold mb-4 text-gray-800">Recent Transactions</h2>
      
      {transactions.length === 0 ? (
        <p className="text-gray-500 text-center py-8">No transactions found. Add your first transaction above!</p>
      ) : (
        <div className="space-y-3">
          {transactions.map((transaction) => (
            <div
              key={transaction.id}
              className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50"
            >
              <div className="flex-1">
                <div className="flex items-center gap-3">
                  <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                    transaction.type === 'income'
                      ? 'bg-green-100 text-green-800'
                      : 'bg-red-100 text-red-800'
                  }`}>
                    {transaction.type === 'income' ? '+' : '-'}
                    ${transaction.amount.toFixed(2)}
                  </span>
                  <span className="font-medium text-gray-900">{transaction.description}</span>
                  {transaction.category && (
                    <span className="text-sm text-gray-500">({transaction.category})</span>
                  )}
                </div>
                <p className="text-sm text-gray-500 mt-1">{transaction.date}</p>
              </div>
              
              <button
                onClick={() => onDelete(transaction.id)}
                className="text-red-600 hover:text-red-800 font-medium text-sm"
              >
                Delete
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// Date Filter Component
const DateFilter = ({ startDate, endDate, onDateChange }) => {
  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
      <h2 className="text-2xl font-bold mb-4 text-gray-800">Filter by Date Range</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Start Date
          </label>
          <input
            type="date"
            value={startDate}
            onChange={(e) => onDateChange('startDate', e.target.value)}
            className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            End Date
          </label>
          <input
            type="date"
            value={endDate}
            onChange={(e) => onDateChange('endDate', e.target.value)}
            className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        <div className="flex items-end">
          <button
            onClick={() => onDateChange('clear', '')}
            className="w-full bg-gray-600 text-white py-3 px-4 rounded-lg font-semibold hover:bg-gray-700 transition-colors"
          >
            Clear Filters
          </button>
        </div>
      </div>
    </div>
  );
};

// Main App Component
function App() {
  const [transactions, setTransactions] = useState([]);
  const [summary, setSummary] = useState({});
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [loading, setLoading] = useState(true);

  const fetchTransactions = async () => {
    try {
      const params = new URLSearchParams();
      if (startDate) params.append('start_date', startDate);
      if (endDate) params.append('end_date', endDate);
      
      const response = await axios.get(`${API}/transactions?${params}`);
      setTransactions(response.data);
    } catch (error) {
      console.error('Error fetching transactions:', error);
    }
  };

  const fetchSummary = async () => {
    try {
      const params = new URLSearchParams();
      if (startDate) params.append('start_date', startDate);
      if (endDate) params.append('end_date', endDate);
      
      const response = await axios.get(`${API}/transactions/summary?${params}`);
      setSummary(response.data);
    } catch (error) {
      console.error('Error fetching summary:', error);
    }
  };

  const handleDateChange = (type, value) => {
    if (type === 'clear') {
      setStartDate('');
      setEndDate('');
    } else if (type === 'startDate') {
      setStartDate(value);
    } else if (type === 'endDate') {
      setEndDate(value);
    }
  };

  const handleDeleteTransaction = async (transactionId) => {
    if (window.confirm('Are you sure you want to delete this transaction?')) {
      try {
        await axios.delete(`${API}/transactions/${transactionId}`);
        fetchData();
      } catch (error) {
        console.error('Error deleting transaction:', error);
        alert('Error deleting transaction. Please try again.');
      }
    }
  };

  const fetchData = async () => {
    setLoading(true);
    await Promise.all([fetchTransactions(), fetchSummary()]);
    setLoading(false);
  };

  useEffect(() => {
    fetchData();
  }, [startDate, endDate]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading your balance sheet...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100">
      <div className="container mx-auto px-4 py-8">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Business Balance Sheet
          </h1>
          <p className="text-lg text-gray-600">
            Track your business income, expenses, and profit/loss
          </p>
        </div>

        <SummaryCards summary={summary} />
        
        <DateFilter 
          startDate={startDate}
          endDate={endDate}
          onDateChange={handleDateChange}
        />

        <TransactionForm onTransactionAdded={fetchData} />

        <TransactionList 
          transactions={transactions}
          onDelete={handleDeleteTransaction}
        />
      </div>
    </div>
  );
}

export default App;