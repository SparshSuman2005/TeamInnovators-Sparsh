import streamlit as st

from chatbot import initialize_chatbot

st.set_page_config(
    page_title="Campus Helpdesk",
    page_icon="🎓",
    layout="wide"
)

st.title("🎓 Campus Helpdesk Assistant")

st.write("Ask any question related to admissions, hostel, finance, academics, examinations, etc.")

# Initialize chatbot once
if "rag" not in st.session_state:
    with st.spinner("Loading chatbot..."):
        rag, config, vector_db = initialize_chatbot()
        st.session_state.rag = rag
        st.session_state.vector_db = vector_db

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous messages
for message in st.session_state.messages:

    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
question = st.chat_input("Ask your question")

if question:

    st.session_state.messages.append(
        {
            "role": "user",
            "content": question
        }
    )

    with st.chat_message("user"):
        st.markdown(question)

    with st.spinner("Searching university documents..."):

        result = st.session_state.rag.query(question)

    answer = result["answer"]

    sources = result["sources"]

    departments = result["departments"]

    routed = result["predicted_department"]

    response = answer

    response += "\n\n---"

    response += f"\n**Department:** {routed}"

    if departments:
        response += "\n\n**Departments Referenced:**\n"

        for dept in departments:
            response += f"- {dept}\n"

    if sources:
        response += "\n\n**Sources:**\n"

        for source in sources:
            response += f"- {source}\n"

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": response
        }
    )

    with st.chat_message("assistant"):
        st.markdown(response)