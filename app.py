import streamlit as st
import sqlite3
import pandas as pd
import requests
import re
import random
import os
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from openai import OpenAI

# Page Configuration
st.set_page_config(
    page_title="AI Data Analytics Copilot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern UI
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    .main-header {
        font-size: 3rem;
        font-weight: 800;
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #ec4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.2);
        margin: 1rem 0;
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: white;
        margin: 0;
    }
    
    .metric-label {
        font-size: 1rem;
        color: rgba(255, 255, 255, 0.8);
        margin-top: 0.5rem;
    }
    
    .section-header {
        font-size: 1.5rem;
        font-weight: 700;
        color: #667eea;
        margin: 2rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 3px solid #667eea;
    }
    
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }
</style>
""", unsafe_allow_html=True)

# ===========================
# NVIDIA API CLIENT SETUP
# ===========================

NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "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")

def create_ai_client():
    try:
        return OpenAI(api_key=NVIDIA_API_KEY, base_url="https://integrate.api.nvidia.com/v1")
    except Exception as e:
        st.warning(f"⚠️ AI client initialization failed: {e}")
        return None

client = create_ai_client()

# ===========================
# DATABASE SETUP
# ===========================

def init_database():
    conn = sqlite3.connect("sales.db", check_same_thread=False)
    cursor = conn.cursor()

    cursor.execute("CREATE TABLE IF NOT EXISTS customers (id INTEGER PRIMARY KEY, name TEXT, city TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY, customer_id INTEGER, amount INTEGER, date TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, name TEXT, price INTEGER)")
    cursor.execute("CREATE TABLE IF NOT EXISTS order_items (id INTEGER PRIMARY KEY, order_id INTEGER, product_id INTEGER, quantity INTEGER)")
    cursor.execute("CREATE TABLE IF NOT EXISTS payments (id INTEGER PRIMARY KEY, order_id INTEGER, payment_method TEXT, status TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS employees (id INTEGER PRIMARY KEY, name TEXT, department TEXT)")

    if cursor.execute("SELECT COUNT(*) FROM customers").fetchone()[0] == 0:
        cursor.executemany("INSERT OR IGNORE INTO customers VALUES (?, ?, ?)", [
            (1,'Aman Kumar','Delhi'),(2,'Riya Sharma','Mumbai'),(3,'Rahul Singh','Kolkata'),
            (4,'Sneha Patel','Bangalore'),(5,'Arjun Mehta','Delhi'),(6,'Priya Reddy','Hyderabad'),
            (7,'Vikas Gupta','Mumbai'),(8,'Anita Das','Kolkata'),(9,'Rohit Verma','Pune'),(10,'Kavita Joshi','Bangalore')
        ])
        cursor.executemany("INSERT OR IGNORE INTO products VALUES (?, ?, ?)", [
            (1,'Laptop',50000),(2,'Smartphone',20000),(3,'Tablet',15000),(4,'Headphones',2000),
            (5,'Smartwatch',8000),(6,'Keyboard',1500),(7,'Mouse',800),(8,'Monitor',12000)
        ])
        base_date = datetime(2024, 1, 1)
        orders = [(i, random.randint(1,10), random.randint(500,5000),
                   (base_date + timedelta(days=random.randint(0,90))).strftime('%Y-%m-%d')) for i in range(1,51)]
        cursor.executemany("INSERT OR IGNORE INTO orders VALUES (?, ?, ?, ?)", orders)
        items = [(i, random.randint(1,50), random.randint(1,8), random.randint(1,5)) for i in range(1,81)]
        cursor.executemany("INSERT OR IGNORE INTO order_items VALUES (?, ?, ?, ?)", items)
        payments = [(i, i, random.choice(['UPI','Card','Net Banking','Cash']),
                     random.choices(['Success','Pending','Failed'], weights=[80,15,5])[0]) for i in range(1,51)]
        cursor.executemany("INSERT OR IGNORE INTO payments VALUES (?, ?, ?, ?)", payments)
        cursor.executemany("INSERT OR IGNORE INTO employees VALUES (?, ?, ?)", [
            (1,'Rohit Kumar','Sales'),(2,'Neha Singh','Support'),(3,'Amit Patel','Marketing'),
            (4,'Sonia Sharma','Sales'),(5,'Rajesh Verma','IT'),(6,'Pooja Reddy','HR'),
            (7,'Vikram Mehta','Finance'),(8,'Anjali Gupta','Operations')
        ])
        conn.commit()
    return conn

@st.cache_resource
def get_database_connection():
    return init_database()

conn = get_database_connection()

@st.cache_data(ttl=300)
def load_data():
    try:
        df_customers = pd.read_sql_query("SELECT * FROM customers", conn)
        df_orders = pd.read_sql_query("SELECT * FROM orders", conn)
        df_products = pd.read_sql_query("SELECT * FROM products", conn)
        df_order_items = pd.read_sql_query("SELECT * FROM order_items", conn)
        df_payments = pd.read_sql_query("SELECT * FROM payments", conn)
        df_employees = pd.read_sql_query("SELECT * FROM employees", conn)
        return df_customers, df_orders, df_products, df_order_items, df_payments, df_employees
    except Exception as e:
        st.error(f"Database error: {e}")
        return None, None, None, None, None, None

df_customers, df_orders, df_products, df_order_items, df_payments, df_employees = load_data()

# ===========================
# HELPER FUNCTIONS
# ===========================

def clean_sql(raw_sql):
    if not raw_sql:
        return ""
    cleaned = raw_sql.replace("```sql", "").replace("```", "").strip()
    # Remove any lines that are not SQL (e.g., explanatory text before/after)
    lines = cleaned.split('\n')
    sql_lines = []
    for line in lines:
        stripped = line.strip().upper()
        if stripped.startswith(('SELECT', 'WITH', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER')) or sql_lines:
            sql_lines.append(line)
    return '\n'.join(sql_lines).strip() if sql_lines else cleaned

def generate_ai_response(prompt):
    if client is None:
        return "⚠️ AI service unavailable (client initialization failed)."
    try:
        response = client.chat.completions.create(
            model="meta/llama-3.1-70b-instruct",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1024
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ AI Error: {str(e)}"

def generate_sql(query):
    if client is None:
        st.error("❌ AI service unavailable (client initialization failed). SQL generation disabled.")
        return ""
    import time
    try:
        schema_info = """
        Database Tables:
        - customers(id, name, city)
        - orders(id, customer_id, amount, date)
        - products(id, name, price)
        - order_items(id, order_id, product_id, quantity)
        - payments(id, order_id, payment_method, status)
        - employees(id, name, department)
        """
        prompt = f"""{schema_info}

Convert the following question to a valid SQLite SQL query. Return ONLY the raw SQL query with no explanation, no markdown, no backticks.

Question: {query}

SQL:"""

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = client.chat.completions.create(
                    model="meta/llama-3.1-70b-instruct",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0,
                    max_tokens=256
                )
                return clean_sql(response.choices[0].message.content.strip())
            except Exception as retry_error:
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                else:
                    raise retry_error
    except Exception as e:
        st.error(f"❌ API Connection Error: {str(e)}")
        return ""

def fix_sql_with_ai(bad_sql, error_msg):
    if client is None:
        return None
    try:
        prompt = f"""Fix this SQLite SQL query that produced an error. Return ONLY the corrected raw SQL with no explanation or markdown.

SQL Query:
{bad_sql}

Error Message:
{error_msg}

Fixed SQL:"""
        response = client.chat.completions.create(
            model="meta/llama-3.1-70b-instruct",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=256
        )
        return clean_sql(response.choices[0].message.content)
    except:
        return None

def create_chart(data, chart_type="bar", x_col=None, y_col=None):
    try:
        if chart_type == "bar":
            fig = px.bar(data, x=x_col, y=y_col,
                         color_discrete_sequence=['#667eea'],
                         template='plotly_dark')
        elif chart_type == "line":
            fig = px.line(data, x=x_col, y=y_col,
                          color_discrete_sequence=['#667eea'],
                          template='plotly_dark')
        elif chart_type == "pie":
            fig = px.pie(data, names=x_col, values=y_col,
                         color_discrete_sequence=px.colors.sequential.Purples,
                         template='plotly_dark')
        else:
            fig = px.bar(data, x=x_col, y=y_col, template='plotly_dark')

        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            margin=dict(l=20, r=20, t=40, b=20)
        )
        return fig
    except Exception as e:
        st.error(f"Chart error: {e}")
        return go.Figure()

# ===========================
# MAIN HEADER
# ===========================

st.markdown('<h1 class="main-header">🤖 AI Data Analytics Copilot</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; color: #888; font-size: 1.2rem;">Autonomous Data Pipeline & Analytics Agent · Powered by NVIDIA AI</p>', unsafe_allow_html=True)

# ===========================
# SIDEBAR
# ===========================

with st.sidebar:
    st.markdown("### ⚙️ Control Panel")
    
    st.markdown("---")
    uploaded_file = st.file_uploader("📁 Upload CSV Data", type=["csv"])
    
    if uploaded_file:
        df_upload = pd.read_csv(uploaded_file)
        st.success(f"✅ Loaded {len(df_upload)} rows")
    else:
        df_upload = None
    
    st.markdown("---")
    st.markdown("### ⚡ Quick Actions")
    
    if st.button("📊 Refresh Dashboard", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.chat = []
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 📚 Database Schema")
    
    with st.expander("View Tables"):
        st.code("""
• customers (id, name, city)
• orders (id, customer_id, amount, date)
• products (id, name, price)
• order_items (id, order_id, product_id, quantity)
• payments (id, order_id, payment_method, status)
• employees (id, name, department)
        """)
    
    st.markdown("---")
    st.markdown("### 📈 Statistics")
    
    if df_customers is not None and df_orders is not None:
        st.metric("Total Customers", len(df_customers))
        st.metric("Total Orders", len(df_orders))
        st.metric("Total Revenue", f"₹{df_orders['amount'].sum():,.0f}")
    
    st.markdown("---")
    st.markdown("### 🌤️ Weather")
    
    if st.button("Get Current Weather", use_container_width=True):
        try:
            data = requests.get(
                "https://api.open-meteo.com/v1/forecast?latitude=22.5&longitude=88.3&current_weather=true",
                timeout=10
            ).json()
            w = data["current_weather"]
            st.info(f"🌡️ {w['temperature']}°C\n💨 Wind: {w['windspeed']} km/h")
        except:
            st.error("Weather data unavailable")

# ===========================
# DASHBOARD METRICS
# ===========================

if df_customers is not None and df_orders is not None:
    st.markdown('<div class="section-header">📊 Dashboard Overview</div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{len(df_customers)}</div>
            <div class="metric-label">Total Customers</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{len(df_orders)}</div>
            <div class="metric-label">Total Orders</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">₹{df_orders['amount'].sum():,.0f}</div>
            <div class="metric-label">Total Revenue</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        avg_order = df_orders['amount'].mean()
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">₹{avg_order:,.0f}</div>
            <div class="metric-label">Avg Order Value</div>
        </div>
        """, unsafe_allow_html=True)

# ===========================
# DATA VISUALIZATION TABS
# ===========================

st.markdown('<div class="section-header">📈 Visual Analytics</div>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["📊 Revenue Analysis", "👥 Customer Insights", "📦 Product Analytics", "💳 Payment Stats"])

with tab1:
    if df_orders is not None and df_customers is not None:
        col1, col2 = st.columns(2)
        
        with col1:
            revenue_by_customer = df_orders.groupby('customer_id')['amount'].sum().reset_index()
            revenue_by_customer = revenue_by_customer.merge(
                df_customers[['id', 'name']],
                left_on='customer_id',
                right_on='id'
            )
            fig = create_chart(revenue_by_customer, "bar", "name", "amount")
            fig.update_layout(title="Revenue by Customer")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            if 'date' in df_orders.columns:
                orders_by_date = df_orders.groupby('date')['amount'].sum().reset_index()
                fig = create_chart(orders_by_date, "line", "date", "amount")
                fig.update_layout(title="Revenue Trend")
                st.plotly_chart(fig, use_container_width=True)

with tab2:
    if df_customers is not None:
        col1, col2 = st.columns(2)
        
        with col1:
            city_dist = df_customers['city'].value_counts().reset_index()
            city_dist.columns = ['city', 'count']
            fig = create_chart(city_dist, "pie", "city", "count")
            fig.update_layout(title="Customer Distribution by City")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.dataframe(df_customers, use_container_width=True, height=400)

with tab3:
    if df_products is not None:
        col1, col2 = st.columns(2)
        
        with col1:
            fig = create_chart(df_products, "bar", "name", "price")
            fig.update_layout(title="Product Prices")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.dataframe(df_products, use_container_width=True, height=400)

with tab4:
    if df_payments is not None:
        col1, col2 = st.columns(2)
        
        with col1:
            payment_dist = df_payments['payment_method'].value_counts().reset_index()
            payment_dist.columns = ['method', 'count']
            fig = create_chart(payment_dist, "pie", "method", "count")
            fig.update_layout(title="Payment Methods Distribution")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            status_dist = df_payments['status'].value_counts().reset_index()
            status_dist.columns = ['status', 'count']
            fig = create_chart(status_dist, "bar", "status", "count")
            fig.update_layout(title="Payment Status")
            st.plotly_chart(fig, use_container_width=True)

# ===========================
# AI CHAT INTERFACE
# ===========================

st.markdown('<div class="section-header">💬 AI Copilot Chat</div>', unsafe_allow_html=True)

if "chat" not in st.session_state:
    st.session_state.chat = []

query = st.chat_input("Ask me anything about your data... 💭")

if query:
    q = query.lower()
    response = ""
    show_data = None
    show_chart = None

    try:
        st.session_state.chat.append(("You", query))

        # Rule-based responses
        if "show all customers" in q or "list customers" in q:
            show_data = df_customers
            response = "✅ Displaying all customers from the database"

        elif "show all orders" in q or "list orders" in q:
            show_data = df_orders
            response = "✅ Displaying all orders from the database"

        elif "show all products" in q or "list products" in q:
            show_data = df_products
            response = "✅ Displaying all products from the database"

        elif re.search(r"(orders?|amount|revenue)\s+(above|greater|more|over|>\s*)\s*(\d+)", q):
            match = re.search(r"(\d+)", q)
            if match:
                num = int(match.group(1))
                show_data = df_orders[df_orders["amount"] > num]
                response = f"✅ Found {len(show_data)} orders above ₹{num}"

        elif "total sales" in q or "total revenue" in q:
            total = df_orders['amount'].sum()
            response = f"💰 **Total Sales/Revenue:** ₹{total:,.0f}"

        elif "average order" in q or "avg order" in q:
            avg = df_orders['amount'].mean()
            response = f"📊 **Average Order Value:** ₹{avg:,.2f}"

        elif "customers from" in q:
            city_match = re.search(r"from\s+(\w+)", q)
            if city_match:
                city = city_match.group(1).capitalize()
                show_data = df_customers[df_customers["city"].str.lower() == city.lower()]
                response = f"✅ Found {len(show_data)} customers from {city}"

        elif "chart" in q or "graph" in q or "visualize" in q:
            if "revenue" in q or "sales" in q:
                show_chart = create_chart(
                    df_orders.groupby('customer_id')['amount'].sum().reset_index(),
                    "bar", "customer_id", "amount"
                )
                show_chart.update_layout(title="Revenue by Customer")
                response = "📊 Generated revenue chart"
            else:
                show_chart = create_chart(df_orders, "bar", "id", "amount")
                show_chart.update_layout(title="Order Amounts")
                response = "📊 Generated chart from order data"

        elif any(keyword in q for keyword in ["show", "list", "find", "get", "select", "which", "who", "how many", "count"]):
            with st.spinner("🤖 Generating SQL query..."):
                sql = generate_sql(query)

                if not sql:
                    response = "❌ Could not generate SQL query. Please rephrase your question."
                else:
                    try:
                        st.code(sql, language="sql")
                        result = pd.read_sql_query(sql, conn)
                        show_data = result
                        response = f"✅ Query executed successfully! Found {len(result)} results."
                    except Exception as e:
                        st.warning(f"⚠️ SQL Error: {str(e)}\n\n🔧 AI is fixing the query...")
                        fixed_sql = fix_sql_with_ai(sql, str(e))
                        if fixed_sql:
                            try:
                                st.code(fixed_sql, language="sql")
                                result = pd.read_sql_query(fixed_sql, conn)
                                show_data = result
                                response = f"✅ Error fixed! Query executed successfully. Found {len(result)} results."
                            except Exception as e2:
                                response = f"❌ Could not fix the error: {str(e2)}"
                        else:
                            response = "❌ AI could not fix the SQL error"

        elif df_upload is not None:
            sample_data = df_upload.head(10).to_string()
            prompt = f"""You are an expert data analyst. Analyze this dataset and provide insights.

Dataset Preview:
{sample_data}

Dataset Info:
- Rows: {len(df_upload)}
- Columns: {list(df_upload.columns)}

Question: {query}

Provide a clear, insightful answer with specific data points."""
            with st.spinner("🤖 Analyzing your data..."):
                response = generate_ai_response(prompt)

        else:
            total_revenue = df_orders['amount'].sum() if df_orders is not None else 0
            context = f"""You are an AI assistant for a data analytics platform.

Available data:
- {len(df_customers) if df_customers is not None else 0} customers
- {len(df_orders) if df_orders is not None else 0} orders
- Total revenue: ₹{total_revenue:,.0f}

Question: {query}

Provide a helpful, concise response."""
            with st.spinner("🤖 Thinking..."):
                response = generate_ai_response(context)

    except Exception as main_error:
        response = f"❌ Error: {str(main_error)}"

    st.session_state.chat.append(("Copilot", response))

    if show_data is not None:
        st.dataframe(show_data, use_container_width=True)

    if show_chart is not None:
        st.plotly_chart(show_chart, use_container_width=True)

# Chat history
st.markdown("---")

for role, msg in st.session_state.chat[-10:]:
    if role == "You":
        with st.chat_message("user"):
            st.markdown(msg)
    else:
        with st.chat_message("assistant"):
            st.markdown(msg)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #888; padding: 2rem;">
    <p>🤖 Powered by NVIDIA AI • Built with Streamlit • Data Analytics Copilot v2.0</p>
    <p style="font-size: 0.9rem;">Autonomous Data Pipeline & Analytics Agent</p>
</div>
""", unsafe_allow_html=True)
