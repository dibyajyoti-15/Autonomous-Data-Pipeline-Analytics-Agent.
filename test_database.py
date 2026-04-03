import sqlite3
import pandas as pd

def test_database():
    """Test database connection and display statistics"""
    
    print("🔍 Testing Database Connection...\n")
    
    try:
        conn = sqlite3.connect("sales.db")
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print("📊 Database Tables:")
        print("-" * 60)
        
        for table in tables:
            table_name = table[0]
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            
            # Get column info
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            col_names = [col[1] for col in columns]
            
            print(f"\n✅ {table_name.upper()}")
            print(f"   Rows: {count}")
            print(f"   Columns: {', '.join(col_names)}")
            
            # Show sample data
            df = pd.read_sql_query(f"SELECT * FROM {table_name} LIMIT 3", conn)
            print(f"\n   Sample Data:")
            print(df.to_string(index=False))
            print("-" * 60)
        
        # Calculate some statistics
        print("\n📈 Quick Statistics:")
        print("-" * 60)
        
        # Total revenue
        cursor.execute("SELECT SUM(amount) FROM orders")
        total_revenue = cursor.fetchone()[0]
        print(f"💰 Total Revenue: ₹{total_revenue:,}")
        
        # Average order value
        cursor.execute("SELECT AVG(amount) FROM orders")
        avg_order = cursor.fetchone()[0]
        print(f"📊 Average Order Value: ₹{avg_order:,.2f}")
        
        # Top customer by revenue
        cursor.execute("""
            SELECT c.name, SUM(o.amount) as total
            FROM customers c
            JOIN orders o ON c.id = o.customer_id
            GROUP BY c.id, c.name
            ORDER BY total DESC
            LIMIT 1
        """)
        top_customer = cursor.fetchone()
        print(f"🏆 Top Customer: {top_customer[0]} (₹{top_customer[1]:,})")
        
        # Most popular payment method
        cursor.execute("""
            SELECT payment_method, COUNT(*) as count
            FROM payments
            GROUP BY payment_method
            ORDER BY count DESC
            LIMIT 1
        """)
        top_payment = cursor.fetchone()
        print(f"💳 Most Popular Payment: {top_payment[0]} ({top_payment[1]} transactions)")
        
        # Success rate
        cursor.execute("SELECT COUNT(*) FROM payments WHERE status = 'Success'")
        success_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM payments")
        total_payments = cursor.fetchone()[0]
        success_rate = (success_count / total_payments) * 100
        print(f"✅ Payment Success Rate: {success_rate:.1f}%")
        
        print("-" * 60)
        print("\n✅ Database test completed successfully!")
        print("🚀 Ready to run: streamlit run app.py\n")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_database()
