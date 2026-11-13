"""Minimal Qanun Streamlit interface."""
import streamlit as st

st.set_page_config(page_title="Qanun", page_icon="⚖️")
st.title("Qanun — droit du travail algérien")
question = st.text_area("Posez votre question")
if st.button("Rechercher", disabled=not question.strip()):
    st.info("TODO: connect retrieval, version selection, and LLM response pipeline.")
    st.subheader("Réponse")
    st.write("Aucune réponse générée pour le moment.")
    st.subheader("Articles cités")
    st.write("Aucun article cité.")
with st.expander("Trace"):
    st.caption("Documents, relations, étapes et appels d’outils apparaîtront ici.")

