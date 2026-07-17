import streamlit as st
import pandas as pd
from xenium_radar.config import load_config
from xenium_radar.storage import Store
st.set_page_config(page_title="Xenium Cancer Data Radar",layout="wide")
config=load_config(); rows=[r.model_dump(mode="json") for r in Store(config["database"]).all()]
df=pd.DataFrame(rows)
if not df.empty and "record_status" in df: df=df[df.record_status != "rejected"]
pages=["Overview","New datasets","Dataset explorer","Cancer type summary","Foundation model papers","Manual review queue","Failed URL checks","Search configuration"]
page=st.sidebar.radio("Page",pages); st.title("Xenium Cancer Data Radar")
if page=="Search configuration": st.code(open("config/settings.yaml",encoding="utf-8").read(),language="yaml")
elif df.empty: st.info("No records yet. Run `python -m xenium_radar update-all`.")
else:
 for col,label in [("record_status","Status"),("journal","Journal"),("repository","Repository"),("xenium_role","Xenium role"),("cancer_type","Cancer type")]:
  selected=st.sidebar.multiselect(label,sorted(df[col].dropna().unique()))
  if selected: df=df[df[col].isin(selected)]
 if page=="Foundation model papers": df=df[df.foundation_model_related]
 if page=="Manual review queue": df=df[df.manual_review_required]
 if page=="New datasets": df=df.sort_values("first_seen_at",ascending=False)
 if page=="Cancer type summary": st.bar_chart(df.cancer_type.value_counts())
 elif page=="Overview":
  a,b,c=st.columns(3);a.metric("Records",len(df));b.metric("Public datasets",int(df.downloadable.fillna(False).sum()));c.metric("Foundation models",int(df.foundation_model_related.sum()));st.dataframe(df)
 else: st.dataframe(df)
 st.download_button("Download filtered CSV",df.to_csv(index=False).encode(),"xenium-radar.csv","text/csv")
