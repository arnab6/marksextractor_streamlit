import streamlit as st
from pymongo import MongoClient
import pandas as pd
import requests
import plotly.express as px

# Connect to MongoDB using the provided connection string
client = MongoClient("mongodb+srv://2023aa05104:9804119164@mongo-cluster.2oaap.mongodb.net/?retryWrites=true&w=majority&appName=mongo-cluster")
db = client["Result_APP"]
collection = db["result"]

# API URL for fetching marks
api_url = "https://arnabghosh.leapcell.app/scrape_v1"

# Function to fetch data from MongoDB
def fetch_data(roll_number, sem_name):
    record = collection.find_one({"roll_number": roll_number, "semester_name": sem_name})
    return record

# Function to save data to MongoDB
def save_data(roll_number, sem_name, subjects_data):
    collection.update_one(
        {"roll_number": roll_number, "semester_name": sem_name},
        {"$set": {"subjects": subjects_data}},
        upsert=True
    )

# Function to fetch marks via the API
def fetch_marks(subject_links):
    response = requests.post(api_url, json=subject_links)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Failed to fetch marks from API. Status code: {response.status_code}")
        return []

# Streamlit app setup
st.title("Exam Marks Extractor and Visualizer")
st.markdown("### Enter your details to fetch subject data")

# Initialize session state for data persistence
if "subjects" not in st.session_state:
    st.session_state.subjects = [{"subject_name": "", "link": ""} for _ in range(4)]

# Inputs
roll_number = st.text_input("Roll Number")
sem_name = st.text_input("Semester Name")
get_data_clicked = st.button("Get Data")

# Get data button
if get_data_clicked:
    if roll_number and sem_name:
        record = fetch_data(roll_number, sem_name)
        if record:
            st.success(f"Data found for Roll No: {roll_number}, Semester: {sem_name}")
            st.session_state.subjects = record["subjects"]
        else:
            st.warning(f"No data found for Roll No: {roll_number}, Semester: {sem_name}. Please add data below.")
            st.session_state.subjects = [{"subject_name": "", "link": ""} for _ in range(4)]
    else:
        st.error("Please provide both Roll Number and Semester Name.")

# Editing subjects
st.markdown("### Edit Subject Data")
edited_subjects = []
subject_links = {}

for i, subject in enumerate(st.session_state.subjects):
    col1, col2 = st.columns(2)
    with col1:
        subject_name = st.text_input(f"Subject {i+1} Name", subject["subject_name"], key=f"subject_name_{i}")
    with col2:
        link = st.text_input(f"Subject {i+1} Link", subject["link"], key=f"link_{i}")
    
    edited_subjects.append({"subject_name": subject_name, "link": link})
    if subject_name and link:
        subject_links[subject_name] = link

# Save button
if st.button("Save Data"):
    save_data(roll_number, sem_name, edited_subjects)
    st.session_state.subjects = edited_subjects
    st.success("Data saved successfully!")

# Fetch marks button
if st.button("Fetch Marks") and subject_links:
    marks_data = fetch_marks(subject_links)
    if marks_data:
        df_marks = pd.DataFrame(marks_data)
        df_marks['marks'] = pd.to_numeric(df_marks['marks'], errors='coerce')
        df_marks['percentile'] = pd.to_numeric(df_marks['percentile'].str.replace('percentile', '').str.strip(), errors='coerce')

        st.markdown("### Marks and Percentile Data")
        st.dataframe(df_marks)

        st.markdown("### Marks Comparison")
        fig_bar = px.bar(df_marks, x='subject', y='marks', color='percentile',
                         title="Marks by Subject with Percentile Color Coding")
        st.plotly_chart(fig_bar)

        fig_scatter = px.scatter(df_marks, x='marks', y='percentile', text='subject',
                                 title="Scatter Plot of Marks vs. Percentile")
        st.plotly_chart(fig_scatter)

# Style updates
st.markdown("""
<style>
    footer {visibility: hidden;}
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        padding: 10px 20px;
        font-size: 16px;
        margin-top: 20px;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)
