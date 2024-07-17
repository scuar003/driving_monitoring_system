import streamlit as st
import random

# Function to generate fake user engagement score
def generate_user_engagement_score():
    return round(random.uniform(76.0, 96.0), 2)

# Function to explain how the score is calculated
def explain_engagement_score():
    st.write("""
    ### How the score is calculated
    The user engagement score is calculated based on several criteria related to the driver's gaze:
    
    - **Road Focus**: Time spent focusing on the road is considered positive.
    - **Mirror Check**: Time spent checking mirrors is considered positive if within a threshold.
    - **Dashboard Check**: Time spent checking the dashboard is considered positive if within a threshold.
    - **Off Road Gaze**: Time spent looking away from the road is considered negative.
    - **Prolonged Check**: Prolonged checks are considered negative if exceeding a threshold.
    - **Closed Eyes**: Time spent with eyes closed is always negative.
    
    Each gaze direction is scored, and the overall engagement score is calculated as a percentage.
    """)

st.title("Driver Monitoring Report")

st.header("User Engagement Score")
score = generate_user_engagement_score()
st.write(f"**Score:** {score}")

if st.button("How the score is calculated"):
    explain_engagement_score()