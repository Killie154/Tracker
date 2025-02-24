import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import json

# Google Sheets Credentials
#credentials = Credentials.from_service_account_file(
#    "/workspaces/Tracker/credentials.json",  # Ensure this file exists in your working directory
#    scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
#)
#client = gspread.authorize(credentials)

service_account_info = json.loads(st.secrets["google_credentials"])
credentials = Credentials.from_service_account_info(service_account_info)
client = gspread.authorize(credentials)

# Exercise dictionary (examples of exercises with muscle groups)
exercise_dict = {
    "Barbell Squats": {"muscle": "Quads", "sets": 4, "reps": 8},
    "Hip Thrusts": {"muscle": "Glutes", "sets": 3, "reps": 8},
    "Standing Calf Raise": {"muscle": "Calves", "sets": 4, "reps": 12},
    "Cable Crunches": {"muscle": "Core", "sets": 3, "reps": 12},
    "Plank": {"muscle": "Core", "sets": 3, "time": 30},  # Plank uses time instead of reps
    "Pull-ups": {"muscle": "Back", "sets": 3, "reps": 8},
    "Barbell Rows": {"muscle": "Back", "sets": 3, "reps": 8},
    "Incline Dumbbell Curls": {"muscle": "Biceps", "sets": 3, "reps": 8},
}

# Function to append data to Google Sheets
def append_to_google_sheet(sheet_name, sheet_index, data):
    sheet = client.open(sheet_name).get_worksheet(sheet_index)  # Open the specific sheet
    sheet.append_row(data)  # Append data as a new row

# Load exercise data from Google Sheets
sheet = client.open("Exercise template").sheet1
exercise_data = sheet.get_all_records()

# Load weight data from the second worksheet
weight_sheet = client.open("Exercise template").get_worksheet(1)
weight_data = weight_sheet.get_all_records()

df_exercise = pd.DataFrame(exercise_data)
df_weight = pd.DataFrame(weight_data)


def page_1():
    st.title("Workout Progress Breakdown")

    #Adding some breathing room.
    st.write("")
    st.write("")
    st.write("")
    st.write("")

    col1, col2 = st.columns(2)
    #Adding some breathing room.

    st.write("")
    st.write("")
    st.write("")
    st.write("")
    # Exercise volume bar chart
    if not df_exercise.empty:
        exercise_volume = df_exercise.groupby("Exercise")["Rep"].sum()
        col1.bar_chart(exercise_volume)

    # Debug: Print column names
    #st.write("Columns in exercise data:", df_exercise.columns.tolist())

    # Most frequently targeted muscle group
# Most frequently targeted muscle group
    if "Muscle" in df_exercise.columns:
        muscle_counts = df_exercise["Muscle"].value_counts()
        if not muscle_counts.empty:
            top_muscle = muscle_counts.idxmax()  # Finds the most frequent muscle group
            col2.markdown(
                f"<h2 style='text-align: center;'>Top Muscle Group Targeted:</h2>"
                f"<h1 style='text-align: center; color: #89CFF0;'>{top_muscle}</h1>",
                unsafe_allow_html=True)

        else:
            col2.write("No muscle group data available.")
    else:
        col2.write("Column 'Muscle' not found in data.")

    col3, col4 = st.columns(2)
    
    # Current weight, target weight, and weight left to lose
    if not df_weight.empty:
        df_weight["Date"] = pd.to_datetime(df_weight["Date"])
        df_weight.sort_values("Date", inplace=True)
        current_weight = df_weight["Weight"].iloc[-1]
        target_weight = 75
        weight_left = max(0, current_weight - target_weight)
        col3.markdown(
            f"<h2 style='color: white;'>Current Weight:</h2>"
            f"<h1 style='color: #89CFF0;'>{current_weight} kg/lbs</h1>"
            f"<h2 style='color: white;'>Target Weight:</h2>"
            f"<h1 style='color: #89CFF0;'>{target_weight} kg/lbs</h1>"
            f"<h2 style='color: white;'>Weight Left to Lose:</h2>"
            f"<h1 style='color: #89CFF0;'>{weight_left} kg/lbs</h1>",
            unsafe_allow_html=True
        )
        # Weight loss over time graph
        fig, ax = plt.subplots()
        ax.plot(df_weight["Date"], df_weight["Weight"], marker='o', linestyle='-')
        ax.set_xlabel("Date")
        ax.set_ylabel("Weight (kg/lbs)")
        ax.set_title("Weight Loss Over Time")
        col4.pyplot(fig)
# Page 2: Exercise Tracker
def page_2():
    st.title("Exercise Tracker 🏋️")
    
    selected_date = datetime.today().strftime("%Y-%m-%d")

    # Initialize session state for exercises
    if "exercises_data" not in st.session_state:
        st.session_state.exercises_data = []

    # Function to add exercise
    def add_exercise():
        exercise = st.selectbox("Which exercise did you do?", list(exercise_dict.keys()))
        sets = exercise_dict[exercise]["sets"]

        # Handle reps or time
        if "time" in exercise_dict[exercise]:
            reps_or_time = st.number_input("Duration (seconds)", min_value=1, value=exercise_dict[exercise]["time"], step=1)
        else:
            reps_or_time = st.number_input("Repetitions", min_value=1, value=exercise_dict[exercise]["reps"], step=1)

        sets_input = st.number_input("Number of sets", min_value=1, value=sets, step=1)

        # Optional weight input
        weight = st.text_input("Weight used (kg or lbs) [Optional]", "")

        if st.button("Add Exercise"):
            muscle = exercise_dict[exercise]["muscle"]
            exercise_data = [
                selected_date,
                exercise,
                sets_input,
                reps_or_time,
                muscle,
                weight if weight else "N/A",  # Default "N/A" if empty
            ]
            st.session_state.exercises_data.append(exercise_data)
            st.success(f"{exercise} added!")

    # Show exercises added so far in a list format
    st.write("### 🏋️ Exercises Added So Far:")
    if st.session_state.exercises_data:
        for i, exercise in enumerate(st.session_state.exercises_data, 1):
            date, name, sets, reps_or_time, muscle, weight = exercise
            st.write(f"**{i}. {name}** - {sets} sets of {reps_or_time} ({muscle})" + (f", Weight: {weight}" if weight != "N/A" else ""))
    else:
        st.write("No exercises added yet.")

    # Submit to Google Sheets
    if st.button("Submit Exercises"):
        if st.session_state.exercises_data:
            try:
                sheet.append_rows(st.session_state.exercises_data, value_input_option="USER_ENTERED")
                st.success("Exercises saved!")
                st.session_state.exercises_data = []  # Clear the stored data
            except Exception as e:
                st.error(f"Failed to save exercises: {e}")
        else:
            st.warning("Add at least one exercise first.")
    add_exercise()

# Page 3: Weight Tracker (Calorie & Body Weight)
def page_3():
    st.title("Weight Tracker ⚖️")

    # Automatically set today's date
    selected_date = datetime.today().strftime("%Y-%m-%d")
    st.write(f"📅 Today is  {selected_date}")

    # User input fields
    calories = st.number_input("Calorie Intake", min_value=0, step=1, format="%d")
    body_weight = st.number_input("Current Body Weight (kg or lbs)", min_value=0.0, step=0.1, format="%.1f")

    # Submit button
    if st.button("Submit Info"):
        if calories > 0 and body_weight > 0:
            data = [selected_date, calories, body_weight]
            append_to_google_sheet("Exercise template", 1, data)  # Sheet 2
            st.success("✅ Thank you!")
        else:
            st.warning("⚠️ Please enter valid values for both fields.")

# Sidebar navigation
st.sidebar.header("Where are we going?")
page = st.sidebar.radio("Breakdown", ["Metrics", "Exercise Tracker", "Weight Tracker"])

# Render content based on the selected page
if page == "Metrics":
    page_1()
elif page == "Exercise Tracker":
    page_2()
elif page == "Weight Tracker":
    page_3()
