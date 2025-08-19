import streamlit as st
import requests
import pandas as pd
import json
from datetime import datetime
import base64
from typing import Dict, List, Optional

# Page configuration
st.set_page_config(
    page_title="WooCommerce Dashboard",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #2E8B57;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.5rem;
        color: #4682B4;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .success-message {
        color: #28a745;
        font-weight: bold;
    }
    .error-message {
        color: #dc3545;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

class WooCommerceAPI:
    def __init__(self, base_url: str, consumer_key: str, consumer_secret: str):
        self.base_url = base_url.rstrip('/')
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.auth = (consumer_key, consumer_secret)
    
    def get_products(self, per_page: int = 10, page: int = 1) -> Dict:
        """Fetch products from WooCommerce"""
        try:
            url = f"{self.base_url}/wp-json/wc/v3/products"
            params = {
                'per_page': per_page,
                'page': page,
                'status': 'publish'
            }
            response = requests.get(url, auth=self.auth, params=params)
            response.raise_for_status()
            return {
                'success': True,
                'data': response.json(),
                'total_pages': int(response.headers.get('X-WP-TotalPages', 1)),
                'total_items': int(response.headers.get('X-WP-Total', 0))
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_subscriptions(self, per_page: int = 10, page: int = 1) -> Dict:
        """Fetch subscriptions from WooCommerce"""
        try:
            url = f"{self.base_url}/wp-json/wc/v3/subscriptions"
            params = {
                'per_page': per_page,
                'page': page
            }
            response = requests.get(url, auth=self.auth, params=params)
            response.raise_for_status()
            return {
                'success': True,
                'data': response.json(),
                'total_pages': int(response.headers.get('X-WP-TotalPages', 1)),
                'total_items': int(response.headers.get('X-WP-Total', 0))
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def test_connection(self) -> Dict:
        """Test API connection"""
        try:
            url = f"{self.base_url}/wp-json/wc/v3/system_status"
            response = requests.get(url, auth=self.auth)
            response.raise_for_status()
            return {'success': True, 'message': 'Connection successful!'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

def init_session_state():
    """Initialize session state variables"""
    if 'api_configured' not in st.session_state:
        st.session_state.api_configured = False
    if 'wc_api' not in st.session_state:
        st.session_state.wc_api = None
    if 'products_data' not in st.session_state:
        st.session_state.products_data = None
    if 'subscriptions_data' not in st.session_state:
        st.session_state.subscriptions_data = None

def sidebar_config():
    """Sidebar configuration for API credentials"""
    st.sidebar.title("🔐 API Configuration")
    
    # API Credentials Form
    with st.sidebar.form("api_config"):
        st.markdown("### WooCommerce API Settings")
        
        base_url = st.text_input(
            "Store URL",
            placeholder="https://yourstore.com",
            help="Your WooCommerce store URL"
        )
        
        consumer_key = st.text_input(
            "Consumer Key",
            type="password",
            help="WooCommerce REST API Consumer Key"
        )
        
        consumer_secret = st.text_input(
            "Consumer Secret",
            type="password",
            help="WooCommerce REST API Consumer Secret"
        )
        
        use_live_keys = st.checkbox(
            "Use Live API Keys",
            help="Check if using production/live keys"
        )
        
        submitted = st.form_submit_button("Connect to WooCommerce")
        
        if submitted:
            if base_url and consumer_key and consumer_secret:
                # Create API instance
                st.session_state.wc_api = WooCommerceAPI(base_url, consumer_key, consumer_secret)
                
                # Test connection
                with st.spinner("Testing connection..."):
                    result = st.session_state.wc_api.test_connection()
                
                if result['success']:
                    st.session_state.api_configured = True
                    st.success("✅ Connected successfully!")
                    st.sidebar.markdown(f"**Environment:** {'🔴 Live' if use_live_keys else '🟡 Test'}")
                else:
                    st.session_state.api_configured = False
                    st.error(f"❌ Connection failed: {result['error']}")
            else:
                st.error("Please fill in all required fields")
    
    # Connection Status
    if st.session_state.api_configured:
        st.sidebar.success("🟢 Connected")
    else:
        st.sidebar.error("🔴 Not Connected")
    
    # Navigation
    st.sidebar.markdown("---")
    return st.sidebar.selectbox(
        "📍 Navigate to:",
        ["Dashboard", "Products", "Subscriptions", "API Testing"]
    )

def display_products():
    """Display products section"""
    st.markdown('<h2 class="section-header">🛍️ Products</h2>', unsafe_allow_html=True)
    
    if not st.session_state.api_configured:
        st.warning("Please configure your API credentials in the sidebar first.")
        return
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        per_page = st.selectbox("Items per page:", [10, 20, 50, 100], index=0)
    
    with col2:
        page = st.number_input("Page:", min_value=1, value=1)
    
    with col3:
        if st.button("🔄 Refresh Products"):
            st.session_state.products_data = None
    
    # Fetch products
    if st.session_state.products_data is None:
        with st.spinner("Loading products..."):
            result = st.session_state.wc_api.get_products(per_page=per_page, page=page)
            st.session_state.products_data = result
    
    if st.session_state.products_data['success']:
        products = st.session_state.products_data['data']
        total_items = st.session_state.products_data['total_items']
        total_pages = st.session_state.products_data['total_pages']
        
        # Display metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Products", total_items)
        with col2:
            st.metric("Current Page", f"{page}/{total_pages}")
        with col3:
            st.metric("Showing", len(products))
        
        # Products table
        if products:
            products_df = pd.DataFrame([
                {
                    'ID': p['id'],
                    'Name': p['name'],
                    'Type': p['type'],
                    'Status': p['status'],
                    'Price': f"${p['price']}" if p['price'] else 'Free',
                    'Stock': p.get('stock_quantity', 'N/A'),
                    'Categories': ', '.join([cat['name'] for cat in p['categories']]),
                    'Date Created': datetime.fromisoformat(p['date_created'].replace('Z', '+00:00')).strftime('%Y-%m-%d')
                }
                for p in products
            ])
            
            st.dataframe(products_df, use_container_width=True)
            
            # Product details expander
            with st.expander("📝 View Product Details"):
                selected_product = st.selectbox(
                    "Select a product:",
                    options=products,
                    format_func=lambda x: f"{x['name']} (ID: {x['id']})"
                )
                
                if selected_product:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**Basic Information:**")
                        st.write(f"- **Name:** {selected_product['name']}")
                        st.write(f"- **SKU:** {selected_product.get('sku', 'N/A')}")
                        st.write(f"- **Type:** {selected_product['type']}")
                        st.write(f"- **Status:** {selected_product['status']}")
                        st.write(f"- **Price:** ${selected_product['price']}")
                    
                    with col2:
                        st.write("**Additional Details:**")
                        st.write(f"- **Stock Quantity:** {selected_product.get('stock_quantity', 'N/A')}")
                        st.write(f"- **Weight:** {selected_product.get('weight', 'N/A')}")
                        st.write(f"- **Dimensions:** {selected_product.get('dimensions', {}).get('length', 'N/A')}")
                        st.write(f"- **Reviews Count:** {selected_product.get('rating_count', 0)}")
                    
                    if selected_product.get('description'):
                        st.write("**Description:**")
                        st.write(selected_product['description'])
        else:
            st.info("No products found.")
    else:
        st.error(f"Error loading products: {st.session_state.products_data['error']}")

def display_subscriptions():
    """Display subscriptions section"""
    st.markdown('<h2 class="section-header">🔄 Subscriptions</h2>', unsafe_allow_html=True)
    
    if not st.session_state.api_configured:
        st.warning("Please configure your API credentials in the sidebar first.")
        return
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        per_page = st.selectbox("Subscriptions per page:", [10, 20, 50], index=0)
    
    with col2:
        page = st.number_input("Page:", min_value=1, value=1, key="sub_page")
    
    with col3:
        if st.button("🔄 Refresh Subscriptions"):
            st.session_state.subscriptions_data = None
    
    # Fetch subscriptions
    if st.session_state.subscriptions_data is None:
        with st.spinner("Loading subscriptions..."):
            result = st.session_state.wc_api.get_subscriptions(per_page=per_page, page=page)
            st.session_state.subscriptions_data = result
    
    if st.session_state.subscriptions_data['success']:
        subscriptions = st.session_state.subscriptions_data['data']
        total_items = st.session_state.subscriptions_data['total_items']
        total_pages = st.session_state.subscriptions_data['total_pages']
        
        # Display metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Subscriptions", total_items)
        with col2:
            st.metric("Current Page", f"{page}/{total_pages}")
        with col3:
            st.metric("Showing", len(subscriptions))
        
        # Subscriptions table
        if subscriptions:
            subs_df = pd.DataFrame([
                {
                    'ID': s['id'],
                    'Status': s['status'],
                    'Total': f"${s['total']}",
                    'Customer': f"{s['billing']['first_name']} {s['billing']['last_name']}",
                    'Email': s['billing']['email'],
                    'Start Date': datetime.fromisoformat(s['date_created'].replace('Z', '+00:00')).strftime('%Y-%m-%d'),
                    'Next Payment': s.get('next_payment_date', 'N/A')
                }
                for s in subscriptions
            ])
            
            st.dataframe(subs_df, use_container_width=True)
            
            # Subscription details expander
            with st.expander("📝 View Subscription Details"):
                selected_subscription = st.selectbox(
                    "Select a subscription:",
                    options=subscriptions,
                    format_func=lambda x: f"ID: {x['id']} - {x['billing']['first_name']} {x['billing']['last_name']}"
                )
                
                if selected_subscription:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**Subscription Info:**")
                        st.write(f"- **ID:** {selected_subscription['id']}")
                        st.write(f"- **Status:** {selected_subscription['status']}")
                        st.write(f"- **Total:** ${selected_subscription['total']}")
                        st.write(f"- **Currency:** {selected_subscription['currency']}")
                    
                    with col2:
                        billing = selected_subscription['billing']
                        st.write("**Customer Info:**")
                        st.write(f"- **Name:** {billing['first_name']} {billing['last_name']}")
                        st.write(f"- **Email:** {billing['email']}")
                        st.write(f"- **Phone:** {billing.get('phone', 'N/A')}")
                        st.write(f"- **Company:** {billing.get('company', 'N/A')}")
                    
                    # Line items
                    st.write("**Items:**")
                    for item in selected_subscription.get('line_items', []):
                        st.write(f"- {item['name']} (Qty: {item['quantity']}) - ${item['total']}")
        else:
            st.info("No subscriptions found.")
    else:
        st.error(f"Error loading subscriptions: {st.session_state.subscriptions_data['error']}")

def display_api_testing():
    """Display API testing section"""
    st.markdown('<h2 class="section-header">🧪 API Testing</h2>', unsafe_allow_html=True)
    
    if not st.session_state.api_configured:
        st.warning("Please configure your API credentials in the sidebar first.")
        return
    
    # Connection test
    col1, col2 = st.columns([1, 2])
    
    with col1:
        if st.button("🔍 Test Connection"):
            with st.spinner("Testing..."):
                result = st.session_state.wc_api.test_connection()
            
            if result['success']:
                st.success(result['message'])
            else:
                st.error(f"Connection failed: {result['error']}")
    
    with col2:
        st.info("Test your WooCommerce API connection")
    
    # Raw API endpoint testing
    st.markdown("### 🛠️ Custom Endpoint Testing")
    
    with st.form("custom_endpoint"):
        endpoint = st.text_input(
            "Endpoint (relative to /wp-json/wc/v3/)",
            placeholder="products",
            help="Enter the endpoint you want to test (e.g., 'products', 'orders', 'customers')"
        )
        
        method = st.selectbox("HTTP Method", ["GET", "POST", "PUT", "DELETE"])
        
        params = st.text_area(
            "Parameters (JSON format)",
            placeholder='{"per_page": 10, "status": "publish"}',
            help="Enter parameters in JSON format"
        )
        
        if st.form_submit_button("🚀 Send Request"):
            if endpoint:
                try:
                    url = f"{st.session_state.wc_api.base_url}/wp-json/wc/v3/{endpoint}"
                    
                    # Parse parameters
                    request_params = {}
                    if params.strip():
                        request_params = json.loads(params)
                    
                    # Make request
                    with st.spinner("Sending request..."):
                        if method == "GET":
                            response = requests.get(url, auth=st.session_state.wc_api.auth, params=request_params)
                        elif method == "POST":
                            response = requests.post(url, auth=st.session_state.wc_api.auth, json=request_params)
                        elif method == "PUT":
                            response = requests.put(url, auth=st.session_state.wc_api.auth, json=request_params)
                        elif method == "DELETE":
                            response = requests.delete(url, auth=st.session_state.wc_api.auth, params=request_params)
                    
                    # Display response
                    st.write(f"**Status Code:** {response.status_code}")
                    
                    if response.status_code < 400:
                        st.success("Request successful!")
                        try:
                            response_json = response.json()
                            st.json(response_json)
                        except:
                            st.text(response.text)
                    else:
                        st.error("Request failed!")
                        st.text(response.text)
                        
                except json.JSONDecodeError:
                    st.error("Invalid JSON in parameters")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

def display_dashboard():
    """Display main dashboard"""
    st.markdown('<h2 class="section-header">📊 Dashboard Overview</h2>', unsafe_allow_html=True)
    
    if not st.session_state.api_configured:
        st.warning("Please configure your API credentials in the sidebar to view dashboard data.")
        return
    
    # Quick stats
    col1, col2, col3, col4 = st.columns(4)
    
    with st.spinner("Loading dashboard data..."):
        # Get quick product stats
        products_result = st.session_state.wc_api.get_products(per_page=1)
        if products_result['success']:
            total_products = products_result['total_items']
        else:
            total_products = "Error"
        
        # Get quick subscription stats
        subs_result = st.session_state.wc_api.get_subscriptions(per_page=1)
        if subs_result['success']:
            total_subscriptions = subs_result['total_items']
        else:
            total_subscriptions = "Error"
    
    with col1:
        st.metric("Total Products", total_products)
    
    with col2:
        st.metric("Total Subscriptions", total_subscriptions)
    
    with col3:
        st.metric("API Status", "🟢 Connected" if st.session_state.api_configured else "🔴 Disconnected")
    
    with col4:
        st.metric("Last Updated", datetime.now().strftime("%H:%M:%S"))
    
    # Quick actions
    st.markdown("### 🚀 Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📦 View Products", use_container_width=True):
            st.session_state.page = "Products"
            st.rerun()
    
    with col2:
        if st.button("🔄 View Subscriptions", use_container_width=True):
            st.session_state.page = "Subscriptions"
            st.rerun()
    
    with col3:
        if st.button("🧪 Test API", use_container_width=True):
            st.session_state.page = "API Testing"
            st.rerun()

def main():
    """Main application"""
    # Initialize session state
    init_session_state()
    
    # Header
    st.markdown('<h1 class="main-header">🛒 WooCommerce Dashboard</h1>', unsafe_allow_html=True)
    
    # Sidebar configuration
    page = sidebar_config()
    
    # Main content based on navigation
    if page == "Dashboard":
        display_dashboard()
    elif page == "Products":
        display_products()
    elif page == "Subscriptions":
        display_subscriptions()
    elif page == "API Testing":
        display_api_testing()
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666;'>
            <p>WooCommerce Dashboard | Built with Streamlit</p>
            <p><small>Ensure your API keys have proper read permissions for WooCommerce REST API</small></p>
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
