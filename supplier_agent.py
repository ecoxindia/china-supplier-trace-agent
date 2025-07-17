# supplier_agent.py - Main Streamlit app
import streamlit as st
import pandas as pd
import socket
import requests
from bs4 import BeautifulSoup

st.set_page_config(page_title="China Supplier Trace Agent", layout="wide")
st.title("?? China Supplier Search and DNS Trace Agent")

# Sidebar Inputs
st.sidebar.header("Search Parameters")
product_name = st.sidebar.text_input("Product Name", placeholder="e.g., PET Mesh")
product_spec = st.sidebar.text_input("Product Specification", placeholder="e.g., 2.5mm PET monofilament")
hs_code = st.sidebar.text_input("HS Code", placeholder="e.g., 56081900")
directories = st.sidebar.multiselect("Directories to Search",
    ["Alibaba", "Made-in-China", "GlobalSources", "1688", "HC360"],
    default=["Made-in-China"]
)

additional_dir = st.sidebar.text_input("Add Additional Directory URL")
if additional_dir:
    directories.append(additional_dir)

start_search = st.sidebar.button("Start Search")

# DNS Resolution
def dns_check(url):
    try:
        domain = url.split("//")[-1].split("/")[0]
        ip = socket.gethostbyname(domain)
        return "Resolved", ip
    except Exception:
        return "Unresolved", None

# Example scraper for Made-in-China
def scrape_made_in_china(query):
    base_url = "https://www.made-in-china.com/search/product"
    search_url = f"{base_url}?word={query.replace(' ', '+')}"
    resp = requests.get(search_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
    soup = BeautifulSoup(resp.text, 'html.parser')
    results = []
    for div in soup.find_all("div", class_="pro-info")[:5]:
        name = div.find("a", class_="pro-title")
        comp = div.find("a", class_="cmp-name")
        if name and comp:
            website = "https:" + comp.get("href", "")
            dns_status, ip = dns_check(website)
            results.append({
                "Company Name": comp.text.strip(),
                "Website": website,
                "DNS Status": dns_status,
                "Resolved IP": ip,
                "Directory": "Made-in-China"
            })
    return results

# Main logic
if start_search and product_name:
    st.info("?? Starting search...")
    df_rows = []
    query = f"{product_name} {product_spec} {hs_code}"

    if "Made-in-China" in directories:
        try:
            rows = scrape_made_in_china(query)
            df_rows.extend(rows)
            st.success(f"? Found {len(rows)} suppliers on Made-in-China")
        except Exception as e:
            st.error(f"Error scraping Made-in-China: {e}")

    if set(directories) & {"Alibaba", "GlobalSources", "1688", "HC360"}:
        st.warning("?? Additional scrapers not implemented yet.")

    if df_rows:
        df = pd.DataFrame(df_rows)
        st.dataframe(df)
        st.download_button("?? Download CSV", df.to_csv(index=False).encode('utf-8'), "results.csv")
else:
    st.info("Enter product details and click 'Start Search'.")
