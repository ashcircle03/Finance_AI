
import streamlit as st
import requests
import os
import pandas as pd
from streamlit_agraph import agraph, Node, Edge, Config

st.set_page_config(page_title="FinGraph: Financial Context Engine", layout="wide")

st.title("💸 FinGraph: Structured Insight Engine")
st.markdown("Turning unstructured news & **Reports** into Actionable Signals.")

API_URL = os.getenv("API_URL", "http://localhost:8000")

# Sidebar
st.sidebar.header("Search")
try:
    leaders = requests.get(f"{API_URL}/leaders").json()
    ticker = st.sidebar.selectbox("Select a Company", [l['ticker'] for l in leaders])
except:
    st.error("API is offline.")
    ticker = None

if ticker:
    # 1. Fetch Data
    try:
        data = requests.get(f"{API_URL}/search/{ticker}").json()
    except Exception as e:
        st.error(f"Failed to fetch data: {e}")
        st.stop()
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["📊 Context Graph", "⚡ AI Signals", "📑 Deep Dive (10-K & Financials)"])
    
    with tab1:
        st.subheader(f"Context Graph: {ticker}")
        nodes = []
        edges = []
        
        for n in data['nodes']:
            color = "#f4f4f4"
            size = 25
            if n['type'] == 'Company': 
                color = "#FFD700"
                size = 35
            elif n['type'] == 'Event':
                color = "#87CEEB" 
            elif n['type'] == 'Sector':
                color = "#FFB6C1"
                
            nodes.append(Node(id=n['id'], label=n['label'], size=size, color=color))
            
        for e in data['edges']:
            edges.append(Edge(source=e['source'], target=e['target'], label=e.get('relation', ''), color="#ccc"))
            
        config = Config(width=800, height=500, directed=True, nodeHighlightBehavior=True, highlightColor="#F7A7A6", collapsible=False)
        agraph(nodes=nodes, edges=edges, config=config)

    with tab2:
        st.subheader("AI Signals (Korean)")
        signals = data.get('signals', [])
        if not signals:
            st.info("비정형 데이터에서 추출된 시그널이 없습니다.")
        
        for sig in signals:
            sentiment_color = "gray"
            if sig['sentiment'] == "POSITIVE": sentiment_color = "green"
            elif sig['sentiment'] == "NEGATIVE": sentiment_color = "red"
            
            with st.container():
                st.markdown(f"""
                <div style="border:1px solid #ddd; padding:15px; border-radius:10px; margin-bottom:10px;">
                    <div style="font-size:12px; color:gray; display:flex; justify-content:space-between;">
                        <span>{sig['date']}</span>
                        <span style="font-weight:bold; color:{sentiment_color}">{sig['sentiment']}</span>
                    </div>
                    <h4 style="margin:5px 0;">{sig['type']}</h4>
                    <p style="font-size:14px;">{sig['summary']}</p>
                    <div style="font-size:12px; color:#666; background-color:#f9f9f9; padding:5px; border-radius:5px;">
                        💡 <b>Reason:</b> {sig['reason']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
    with tab3:
        st.subheader("📑 Qualitative & Quantitative Analysis")
        
        # Financial Charts
        fin = data.get('financials')
        if fin:
            st.markdown("### 📈 Financial Performance (Quarterly)")
            
            col_rev, col_inc = st.columns(2)
            
            with col_rev:
                st.markdown("#### Revenue (USD)")
                rev_data = fin.get('revenues', [])
                if rev_data:
                    df_rev = pd.DataFrame(rev_data)
                    df_rev['date'] = pd.to_datetime(df_rev['date'])
                    st.bar_chart(df_rev.set_index('period')['value'])
                else:
                    st.info("No Revenue data available.")
                    
            with col_inc:
                st.markdown("#### Net Income (USD)")
                inc_data = fin.get('net_incomes', [])
                if inc_data:
                    df_inc = pd.DataFrame(inc_data)
                    df_inc['date'] = pd.to_datetime(df_inc['date'])
                    st.line_chart(df_inc.set_index('period')['value'])
                else:
                    st.info("No Net Income data available.")
                    
            st.markdown("---")
            
        else:
             st.warning("No Financial data available. Run the ETL pipeline.")
        
        # 10-K Report
        report = data.get('report')
        if report:
            st.info(f"Analyzed from SEC Filing ({report['year']})")
            
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown("### 🏢 Business Overview")
                st.write(f"**Core:** {report['business_summary']}")
                st.caption(report['detailed_business'])
                
                st.markdown("### ⚔️ Key Competitors")
                for comp in report['competitors']:
                    st.markdown(f"- {comp}")
            
            with col_b:
                st.markdown("### ⚠️ Risk Factors")
                for risk in report['risks']:
                    st.warning(risk)
        else:
            st.warning("No 10-K analysis available.")

    st.markdown("---")
    st.markdown("📰 **Recent News**")
    if data.get('news'):
        for news in data['news']:
            with st.expander(f"{news['date']} - {news['title']}"):
                st.write(f"Source: [Link]({news['url']})")
