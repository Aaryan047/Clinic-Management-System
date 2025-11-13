Clinic Management System

This is a web-based clinic management dashboard built with Streamlit and Supabase. It provides a multi-user, role-based interface for Doctors, Nurses, and Patients to manage appointments and view medical data.

Features

Role-Based Access Control: Separate login and dashboard views for Doctors, Nurses, and Patients.

Doctor Dashboard:

View only your assigned patients and appointments.

Book new appointments for both existing and new patients.

Cancel upcoming appointments.

Patient Dashboard:

View your personal information.

View your full history of appointments and prescriptions.

Book new appointments with any doctor.

Cancel your own upcoming appointments.

Nurse Dashboard:

View all doctors and appointments in the system.

Custom Theming:

Includes a robust light/dark mode toggle with 6 dark themes and 5 light themes.

Custom CSS injection for a fully themed user experience.

Tech Stack

Frontend: Streamlit

Backend & Database: Supabase (PostgreSQL)

Libraries: pandas, supabase-py, python-dotenv

How to Run Locally

Follow these steps to set up and run the project on your local machine.

1. Prerequisites

Python 3.8+

A free Supabase account

A code editor (like VS Code)

2. Clone the Repository

git clone [https://github.com/](https://github.com/)[YOUR_USERNAME]/[YOUR_REPO_NAME].git
cd [YOUR_REPO_NAME]


3. Set Up Supabase

Go to your Supabase project dashboard.

Use the SQL Editor to run a script to create your tables. You will need to create the patient, staff, doctor, nurse, appointment, prescription, etc. tables based on your project's schema.

Fill your tables with some sample data so you can log in.

In your Supabase dashboard, go to Project Settings > API.

Find your Project URL (e.g., https://your-project.supabase.co).

Find your service_role key. Do not use the anon key. The service_role key is required to bypass Row Level Security (RLS) for the login function.

4. Set Up Environment

Install the required Python packages:

pip install -r requirements.txt


Create a file named .env in the root of the project:

SUPABASE_URL="YOUR_PROJECT_URL_HERE"
SUPABASE_KEY="YOUR_SERVICE_ROLE_KEY_HERE"


(Recommended) Create a folder named .streamlit and add a config.toml file inside it:

Folder: .streamlit/

File: config.toml

Add this text to config.toml to force the app to start in light mode, which prevents theme mismatches:

[theme]
base="light"


5. Run the App

Make sure you have fully stopped and restarted the app if it was running.

Run the Streamlit app from your terminal:

streamlit run app.py


The app should open in your browser. You can now log in using the sample data you created in Supabase.

License

This project is licensed under the MIT License. See the LICENSE file for details.
