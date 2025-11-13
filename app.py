import streamlit as st
import os
from dotenv import load_dotenv
from supabase import create_client, Client
import pandas as pd
from typing import Optional, Tuple, Any, Dict
import datetime

load_dotenv()

# --- PAGE CONFIG ---
# This should be the first Streamlit command
st.set_page_config(page_title="Clinic Frontend", layout="wide")


# --- THEME DEFINITIONS ---
THEMES = {
    # Dark themes
    "Dark": {
        "primary": "#D32F2F", "background": "#0E1117", "secondary_bg": "#262730",
        "text": "#FAFAFA", "button_text": "#FFFFFF", "plot_bg": "#1E1E1E",
        "paper_bg": "#0E1117", "grid": "#3E3E3E", "type": "dark"
    },
    "Ocean": {
        "primary": "#00CED1", "background": "#0A192F", "secondary_bg": "#172A45",
        "text": "#CCD6F6", "button_text": "#0A192F", "plot_bg": "#0A192F",
        "paper_bg": "#0A192F", "grid": "#233554", "type": "dark"
    },
    "Dracula": {
        "primary": "#BD93F9", "background": "#282A36", "secondary_bg": "#44475A",
        "text": "#F8F8F2", "button_text": "#F8F8F2", "plot_bg": "#282A36",
        "paper_bg": "#282A36", "grid": "#44475A", "type": "dark"
    },
    # Light themes
    "Light Classic": {
        "primary": "#1976D2", "background": "#FFFFFF", "secondary_bg": "#F5F5F5",
        "text": "#212121", "button_text": "#FFFFFF", "plot_bg": "#FFFFFF",
        "paper_bg": "#FFFFFF", "grid": "#E0E0E0", "type": "light"
    },
    "Mint Fresh": {
        "primary": "#00695C", "background": "#F2F7F5", "secondary_bg": "#E6F3F0",
        "text": "#212121", "button_text": "#FFFFFF", "plot_bg": "#F2F7F5",
        "paper_bg": "#F2F7F5", "grid": "#B2DFDB", "type": "light"
    },
    "Rose Gold": {
        "primary": "#B71C1C", "background": "#FFF0F3", "secondary_bg": "#FFE4E8",
        "text": "#212121", "button_text": "#FFFFFF", "plot_bg": "#FFF0F3",
        "paper_bg": "#FFF0F3", "grid": "#FFCDD2", "type": "light"
    }
}

def apply_custom_css(theme: dict):
    """Apply custom CSS based on selected theme"""
    css = f"""
    <style>
        /* Main app background */
        .stApp {{
            background-color: {theme["background"]};
            color: {theme["text"]};
        }}
        
        /* Sidebar background */
        section[data-testid="stSidebar"] {{
            background-color: {theme["secondary_bg"]} !important;
        }}
        
        /* Sidebar text elements */
        section[data-testid="stSidebar"] .stMarkdown,
        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3,
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] .stRadio label {{
            color: {theme["text"]} !important;
        }}
        
        /* Main content headers */
        .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stTitle {{
            color: {theme["text"]} !important;
        }}

        /* Tabs */
        .stTabs [data-baseweb="tab"] {{
            background-color: {theme["secondary_bg"]};
            color: {theme["text"]};
        }}
        .stTabs [data-baseweb="tab"][aria-selected="true"] {{
            background-color: {theme["background"]};
            border-bottom-color: {theme["primary"]};
            color: {theme["primary"]};
        }}
        
        /* Buttons */
        .stButton > button {{
            background-color: {theme["primary"]};
            color: {theme["button_text"]};
            border: none;
            border-radius: 5px;
            font-weight: 600;
        }}
        .stButton > button:hover {{ opacity: 0.85; }}
        .stButton > button:disabled {{ opacity: 0.4; }}
        
        /* Dataframe */
        .dataframe {{
            background-color: {theme["secondary_bg"]} !important;
        }}
        
        /* Info/Error boxes */
        .stAlert {{
            background-color: {theme["secondary_bg"]};
            color: {theme["text"]};
        }}
        
        /* All input labels */
        .stTextInput label, .stNumberInput label, .stSelectbox label, 
        .stRadio > label, .stDateInput label, .stTimeInput label,
        .stTextArea label {{
            color: {theme["text"]} !important;
        }}

        /* Make radio/selectbox text dark on light themes */
        .stRadio [role="radiogroup"] label > div:last-child,
        .stSelectbox div[data-baseweb="select"] > div {{
            color: {theme["text"]} !important;
        }}

        /* Fix for dark-mode-base text inputs */
        div[data-testid="stTextInput"] div[data-baseweb="input"] > div,
        div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {{
            background-color: {theme["secondary_bg"]};
            border-color: {theme["grid"]};
        }}
        div[data-testid="stTextInput"] input,
        div[data-testid="stSelectbox"] div[data-baseweb="select"] div {{
            color: {theme["text"]} !important;
        }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

# --- END THEME ---


# --- SUPABASE & SESSION STATE ---

@st.cache_resource
def init_supabase() -> Client:
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    
    if not url or not key:
        st.error("Supabase credentials not found. Please configure SUPABASE_URL and SUPABASE_KEY.")
        st.stop()
    
    return create_client(url, key)

supabase = init_supabase()

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_name = None
    st.session_state.user_id = None # Will be stored as an INT
    st.session_state.user_role = None
    st.session_state.patient_id_column = None
    
    # Add default theme states
    st.session_state.selected_theme = "Light Classic"
    st.session_state.theme_mode = "light"

# --- THEME APPLICATION ---
# This must run on *every* page load, before other UI elements
current_theme = THEMES[st.session_state.selected_theme]
apply_custom_css(current_theme)
# --- END THEME APPLICATION ---


# --- FUNCTION DEFINITIONS ---

def find_id_column(table_name: str, id_value: str, possible_columns: list) -> Optional[str]:
    """Find which column name exists and matches the ID value in the given table."""
    
    try:
        numeric_id = int(id_value)
    except ValueError:
        st.error(f"ID must be a number. You entered '{id_value}'.")
        return None 

    for col_name in possible_columns:
        try:
            response = supabase.table(table_name).select("*").eq(col_name, numeric_id).execute()
            if response.data:
                return col_name
        except Exception as e:
            error_str = str(e)
            if "does not exist" not in error_str.lower():
                st.warning(f"Unexpected error checking column '{col_name}' in table '{table_name}': {error_str}")
            continue
    return None

def login(user_id: str, position: str):
    role = None
    id_column = None
    user_name = None
    error_details = []
    
    # Convert to int *once* for all checks
    try:
        numeric_user_id = int(user_id)
    except ValueError:
        st.error(f"ID must be a number. You entered '{user_id}'.")
        return

    try:
        if position == 'Doctor':
            possible_columns = ['doctor_id'] 
            id_column = find_id_column("doctor", user_id, possible_columns) # find_id_column needs the string
            
            if id_column:
                role = "Doctor"
                try:
                    name_response = supabase.table("staff").select("name").eq("staff_id", numeric_user_id).execute()
                    if name_response.data:
                        user_name = name_response.data[0]['name']
                    else:
                        error_details.append(f"Doctor ID '{user_id}' found, but no matching 'staff' record exists to get name.")
                except Exception as e:
                    error_details.append(f"Error fetching staff name: {str(e)}")
            else:
                error_details.append(f"No doctor found with ID '{user_id}' in column 'doctor_id'.")
                
        elif position == 'Nurse':
            possible_columns = ['nurse_id']
            id_column = find_id_column("nurse", user_id, possible_columns)
            
            if id_column:
                role = "Nurse"
                try:
                    name_response = supabase.table("staff").select("name").eq("staff_id", numeric_user_id).execute()
                    if name_response.data:
                        user_name = name_response.data[0]['name']
                    else:
                        error_details.append(f"Nurse ID '{user_id}' found, but no matching 'staff' record exists to get name.")
                except Exception as e:
                    error_details.append(f"Error fetching staff name: {str(e)}")
            else:
                error_details.append(f"No nurse found with ID '{user_id}' in column 'nurse_id'.")
                
        elif position == 'Patient':
            possible_columns = ['patient_id']
            id_column = find_id_column("patient", user_id, possible_columns)
            
            if id_column:
                role = "Patient"
                try:
                    name_response = supabase.table("patient").select("name").eq(id_column, numeric_user_id).execute()
                    if name_response.data:
                        user_name = name_response.data[0]['name']
                        st.session_state.patient_id_column = id_column
                    else:
                        error_details.append(f"Patient ID '{user_id}' found, but couldn't fetch name.")
                except Exception as e:
                    error_details.append(f"Error fetching patient name: {str(e)}")
            else:
                error_details.append(f"No patient found with ID '{user_id}' in column 'patient_id'.")
        
    except Exception as e:
        # This will catch the NameError if find_id_column isn't defined
        error_details.append(f"Database connection error: {str(e)}")
    
    if role and user_name:
        st.session_state.logged_in = True
        st.session_state.user_name = user_name
        st.session_state.user_id = numeric_user_id 
        st.session_state.user_role = role
        st.rerun()
    else:
        if not error_details:
            error_details.append("Invalid credentials. Please check your Position and ID.")
        st.error(f"Login failed: {' | '.join(error_details)}")

def logout():
    st.session_state.logged_in = False
    st.session_state.user_name = None
    st.session_state.user_id = None
    st.session_state.user_role = None
    st.session_state.patient_id_column = None
    st.rerun()

def safe_query(table_name: str, eq_column: Optional[str] = None, eq_value: Optional[Any] = None) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """
    Safely query a Supabase table and return a DataFrame or error message.
    """
    try:
        if eq_column and eq_value is not None:
            response = supabase.table(table_name).select("*").eq(eq_column, eq_value).execute()
        else:
            response = supabase.table(table_name).select("*").execute()
            
        if response.data:
            return pd.DataFrame(response.data), None
        else:
            return None, f"No data found in {table_name} table."
    except Exception as e:
        error_msg = str(e)
        if "infinite recursion" in error_msg.lower():
            return None, f"Database configuration error: Row Level Security policy issue in {table_name}. Please check your Supabase RLS policies."
        elif "does not exist" in error_msg.lower():
            return None, f"Column or table error in {table_name}: {error_msg}"
        else:
            return None, f"Error accessing {table_name}: {error_msg}"

def get_cancellable_appointments(id_column: str, user_id: int) -> pd.DataFrame:
    df, _ = safe_query("appointment", id_column, user_id)
    if df is not None:
        df = df[df['status'] == 'Booked']
        # A more advanced version would join tables to get names
        df['display'] = "Appt ID: " + df['appointment_id'].astype(str) + " on " + df['appointment_datetime'].astype(str)
        return df
    return pd.DataFrame(columns=['appointment_id', 'display'])

def book_appointment(patient_id, doctor_id, clinic_id, appt_datetime, reason):
    try:
        response = supabase.table("appointment").insert({
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "clinic_id": clinic_id,
            "appointment_datetime": appt_datetime,
            "status": "Booked",
            "reason": reason,
            "priority": "Medium"
        }).execute()
        
        if response.data:
            st.success("Appointment booked successfully!")
            st.rerun()
        else:
            st.error(f"Failed to book appointment: {response.error.message if response.error else 'Unknown error'}")
    except Exception as e:
        st.error(f"Error: {str(e)}")

def sign_up_patient(name, email, phone, dob, gender, addr):
    """Handles new patient sign up and logs them in."""
    if not name:
        st.error("Name is a required field.")
        return

    try:
        new_patient_data = {
            "name": name,
            "email": email,
            "phone": phone,
            "date_of_birth": str(dob),
            "gender": gender,
            "address": addr  # <--- FIX: Renamed 'addr' to 'address'
        }
        
        # Insert new patient and get their details back
        response = supabase.table("patient").insert(new_patient_data).execute()
        
        if response.data:
            new_user = response.data[0]
            new_patient_id = new_user['patient_id']
            new_patient_name = new_user['name']
            
            # Log the new user in
            st.session_state.logged_in = True
            st.session_state.user_name = new_patient_name
            st.session_state.user_id = new_patient_id
            st.session_state.user_role = "Patient"
            st.session_state.patient_id_column = "patient_id" # Set this for the dashboard
            
            # <--- FIX: Show the user their new ID
            st.success(f"Welcome, {new_patient_name}! Your account has been created. Your new Patient ID is {new_patient_id}. You are now logged in.")
            st.rerun()
        else:
            st.error(f"Sign up failed: {response.error.message if response.error else 'Unknown error'}")

    except Exception as e:
        st.error(f"An error occurred during sign up: {str(e)}")


def doctor_dashboard():
    st.title("Doctor Dashboard")
    st.write(f"Welcome, Dr. {st.session_state.user_name}!")
    
    tab1, tab2, tab3, tab4 = st.tabs(["My Patients", "My Appointments", "All Payments", "Manage Appointments"])
    
    with tab1:
        st.subheader("My Patients")
        try:
            appt_response = supabase.table("appointment").select("patient_id").eq("doctor_id", st.session_state.user_id).execute()
            if appt_response.data:
                patient_ids = list(set([d['patient_id'] for d in appt_response.data]))
                
                patient_response = supabase.table("patient").select("*").in_("patient_id", patient_ids).execute()
                if patient_response.data:
                    st.dataframe(pd.DataFrame(patient_response.data), use_container_width=True)
                else:
                    st.info("No patient details found for your appointments.")
            else:
                st.info("You do not have any appointments, and therefore no patients listed.")
        except Exception as e:
            st.error(f"Error fetching patients: {str(e)}")

    with tab2:
        st.subheader("My Appointments")
        df, error = safe_query("appointment", "doctor_id", st.session_state.user_id)
        if df is not None:
            st.dataframe(df, use_container_width=True)
        elif error:
            st.error(error)
        else:
            st.info("No appointments found.")
    
    with tab3:
        st.subheader("All Payments")
        df, error = safe_query("payment")
        if df is not None:
            st.dataframe(df, use_container_width=True)
        elif error:
            st.error(error)
        else:
            st.info("No payments found.")

    with tab4:
        st.subheader("Manage Appointments")
        book_tab, cancel_tab = st.tabs(["Book New Appointment", "Cancel Appointment"])

        with book_tab:
            st.subheader("Book New Appointment")
            
            booking_mode = st.radio("Select Patient Type", ["Existing Patient", "New Patient"], horizontal=True)
            
            patients_df, _ = safe_query("patient")
            
            if patients_df is None and booking_mode == "Existing Patient":
                st.warning("Could not load patient list. Please add a new patient.")
                booking_mode = "New Patient"
                
            with st.form("doctor_book_form"):
                patient_id_to_book = None 

                if booking_mode == "Existing Patient":
                    if patients_df is not None:
                        patient_options = {row['name']: row['patient_id'] for index, row in patients_df.iterrows()}
                        selected_patient_name = st.selectbox("Select Existing Patient", options=patient_options.keys())
                        patient_id_to_book = patient_options[selected_patient_name]
                    else:
                        st.error("Patient list is unavailable. Please select 'New Patient'.")
                
                else: # booking_mode == "New Patient"
                    st.subheader("New Patient Details")
                    new_patient_name = st.text_input("Name")
                    new_patient_email = st.text_input("Email")
                    new_patient_phone = st.text_input("Phone")
                    new_patient_dob = st.date_input("Date of Birth", 
                                                    min_value=datetime.date(1900, 1, 1), 
                                                    max_value=datetime.date.today(),
                                                    value=datetime.date(2000, 1, 1))
                    new_patient_gender = st.selectbox("Gender", ["Male", "Female", "Other"])
                    new_patient_addr = st.text_area("Address")
                
                st.divider()
                st.subheader("Appointment Details")
                appt_date = st.date_input("Appointment Date", min_value=datetime.date.today())
                appt_time = st.time_input("Appointment Time", value=datetime.time(9, 0))
                reason = st.text_area("Reason for visit")
                submit_button = st.form_submit_button("Book Appointment")

                if submit_button:
                    if booking_mode == "New Patient":
                        if not new_patient_name:
                            st.error("New patient's Name is required.")
                        else:
                            try:
                                new_patient_data = {
                                    "name": new_patient_name,
                                    "email": new_patient_email,
                                    "phone": new_patient_phone,
                                    "date_of_birth": str(new_patient_dob),
                                    "gender": new_patient_gender,
                                    "address": new_patient_addr # <--- FIX: Renamed 'addr' to 'address'
                                }
                                # Insert new patient and get their ID
                                
                                if insert_response.data:
                                    patient_id_to_book = insert_response.data[0]['patient_id']
                                    st.success(f"Successfully created new patient: {new_patient_name} (ID: {patient_id_to_book})")
                                else:
                                    st.error(f"Failed to create new patient: {insert_response.error.message if insert_response.error else 'Unknown error'}")

                            except Exception as e:
                                st.error(f"Error creating patient: {str(e)}")
                    
                    if patient_id_to_book is not None:
                        doctor_id = st.session_state.user_id
                        clinic_id = 1 # Hardcoding clinic ID 1 as example
                        appt_datetime_str = f"{appt_date} {appt_time}"
                        book_appointment(patient_id_to_book, doctor_id, clinic_id, appt_datetime_str, reason)
                    elif booking_mode == "Existing Patient":
                         st.error("No patient was selected.")

        with cancel_tab:
            st.subheader("Cancel an Appointment")
            cancellable_df = get_cancellable_appointments("doctor_id", st.session_state.user_id)
            
            if not cancellable_df.empty:
                appt_to_cancel_display = st.selectbox("Select appointment to cancel", options=cancellable_df['display'])
                appt_to_cancel_id = cancellable_df[cancellable_df['display'] == appt_to_cancel_display]['appointment_id'].values[0]
                
                if st.button("Cancel Selected Appointment"):
                    cancel_appointment(int(appt_to_cancel_id))
            else:
                st.info("You have no 'Booked' appointments to cancel.")


def nurse_dashboard():
    st.title("Nurse Dashboard")
    st.write(f"Welcome, {st.session_state.user_name}!")
    
    tab1, tab2 = st.tabs(["Assigned Doctors", "Appointments"])
    
    with tab1:
        st.subheader("Assigned Doctors")
        df, error = safe_query("doctor")
        if df is not None:
            st.dataframe(df, use_container_width=True)
        elif error:
            st.error(error)
        else:
            st.info("No doctors found.")
    
    with tab2:
        st.subheader("Appointments")
        df, error = safe_query("appointment")
        if df is not None:
            st.dataframe(df, use_container_width=True)
        elif error:
            st.error(error)
        else:
            st.info("No appointments found.")

def patient_dashboard():
    st.title("Patient Dashboard")
    st.write(f"Welcome, {st.session_state.user_name}!")
    
    tab1, tab2, tab3, tab4 = st.tabs(["My Info", "My Appointments", "My Prescriptions", "Manage Appointments"])
    
    patient_id_col = st.session_state.patient_id_column or "patient_id" 
    
    with tab1:
        st.subheader("My Information")
        df, error = safe_query("patient", patient_id_col, st.session_state.user_id)
        if df is not None and not df.empty:
            patient_info = df.iloc[0].to_dict()
            col1, col2 = st.columns(2)
            items = list(patient_info.items())
            mid = len(items) // 2
            with col1:
                for key, value in items[:mid]:
                    st.write(f"**{key}:** {value}")
            with col2:
                for key, value in items[mid:]:
                    st.write(f"**{key}:** {value}")
        elif error:
            st.error(error)
        else:
            st.info("No patient information found.")
    
    with tab2:
        st.subheader("My Appointments")
        df, error = safe_query("appointment", patient_id_col, st.session_state.user_id)
        if df is not None:
            st.dataframe(df, use_container_width=True)
        elif error:
            st.error(error)
        else:
            st.info("No appointments found.")
    
    with tab3:
        st.subheader("My Prescriptions")
        
        try:
            patient_id = st.session_state.user_id
            
            appt_response = supabase.table("appointment").select("appointment_id").eq("patient_id", patient_id).execute()
            
            if not appt_response.data:
                st.info("No appointments found, so no prescriptions can be shown.")
            else:
                appointment_ids = [d['appointment_id'] for d in appt_response.data]
                
                presc_response = supabase.table("prescription").select("*").in_("appointment_id", appointment_ids).execute()
                
                if presc_response.data:
                    df = pd.DataFrame(presc_response.data)
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("No prescriptions found for your past appointments.")
                    
        except Exception as e:
            st.error(f"Error fetching prescriptions: {str(e)}")

    with tab4:
        st.subheader("Manage Appointments")
        book_tab, cancel_tab = st.tabs(["Book New Appointment", "Cancel Appointment"])

        with book_tab:
            st.subheader("Book New Appointment")
            
            try:
                doc_response = supabase.table("staff").select("staff_id, name").eq("staff_type", "Doctor").execute()
                if doc_response.data:
                    doctor_options = {d['name']: d['staff_id'] for d in doc_response.data}
                    
                    with st.form("patient_book_form"):
                        selected_doc_name = st.selectbox("Select Doctor", options=doctor_options.keys())
                        appt_date = st.date_input("Appointment Date", min_value=datetime.date.today())
                        appt_time = st.time_input("Appointment Time", value=datetime.time(9, 0))
                        reason = st.text_area("Reason for visit")
                        submit_button = st.form_submit_button("Book Appointment")

                        if submit_button:
                            patient_id = st.session_state.user_id
                            doctor_id = doctor_options[selected_doc_name]
                            clinic_id = 1 # Hardcoding clinic ID 1 as example
                            appt_datetime_str = f"{appt_date} {appt_time}"
                            book_appointment(patient_id, doctor_id, clinic_id, appt_datetime_str, reason)
                else:
                    st.error("Could not load doctor list.")
            except Exception as e:
                st.error(f"Error loading doctors: {str(e)}")

        with cancel_tab:
            st.subheader("Cancel an Appointment")
            cancellable_df = get_cancellable_appointments(patient_id_col, st.session_state.user_id)
            
            if not cancellable_df.empty:
                appt_to_cancel_display = st.selectbox("Select appointment to cancel", options=cancellable_df['display'])
                appt_to_cancel_id = cancellable_df[cancellable_df['display'] == appt_to_cancel_display]['appointment_id'].values[0]
                
                if st.button("Cancel Selected Appointment"):
                    cancel_appointment(int(appt_to_cancel_id))
            else:
                st.info("You have no 'Booked' appointments to cancel.")


# --- MAIN APP LOGIC ---
# This part MUST come AFTER all function definitions

if not st.session_state.logged_in:
    # --- LOGIN PAGE ---
    st.title("Clinic Management System")
    
    login_tab, signup_tab = st.tabs(["Login", "Sign Up as New Patient"])
    
    with login_tab:
        st.subheader("Login")
        with st.form("login_form"):
            position = st.selectbox("Select your position:", ["Doctor", "Nurse", "Patient"])
            user_id = st.text_input("ID") 
            submit = st.form_submit_button("Login")
            
            if submit:
                if user_id and position:
                    login(user_id, position)
                else:
                    st.warning("Please select your position and enter your ID.")

    with signup_tab:
        st.subheader("Create a New Patient Account")
        with st.form("signup_form"):
            st.write("Please fill in your details to create an account. Your Patient ID will be automatically generated.")
            
            # Get details for new patient
            new_patient_name = st.text_input("Full Name*")
            new_patient_email = st.text_input("Email")
            new_patient_phone = st.text_input("Phone")
            new_patient_dob = st.date_input("Date of Birth", 
                                            min_value=datetime.date(1900, 1, 1), 
                                            max_value=datetime.date.today(),
                                            value=datetime.date(2000, 1, 1))
            new_patient_gender = st.selectbox("Gender", ["Male", "Female", "Other"])
            new_patient_address = st.text_area("Address") # <--- FIX: Renamed variable
            
            signup_submit = st.form_submit_button("Sign Up")
            
            if signup_submit:
                # Call the new sign up function
                sign_up_patient(
                    new_patient_name, 
                    new_patient_email, 
                    new_patient_phone, 
                    new_patient_dob, 
                    new_patient_gender, 
                    new_patient_address # <--- FIX: Pass the renamed variable
                )

else:
    # --- LOGGED-IN DASHBOARD ---
    with st.sidebar:
        st.write(f"**Logged in as:** {st.session_state.user_name}")
        st.write(f"**Role:** {st.session_state.user_role}")
        st.write(f"**ID:** {st.session_state.user_id}")
        st.divider()
        
        # --- THEME SWITCHER UI ---
        st.subheader("Theme Settings")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Light", use_container_width=True, 
                        disabled=(st.session_state.theme_mode == "light")):
                st.session_state.theme_mode = "light"
                if THEMES[st.session_state.selected_theme]["type"] == "dark":
                    st.session_state.selected_theme = "Light Classic"
                st.rerun()
        
        with col2:
            if st.button("Dark", use_container_width=True,
                        disabled=(st.session_state.theme_mode == "dark")):
                st.session_state.theme_mode = "dark"
                if THEMES[st.session_state.selected_theme]["type"] == "light":
                    st.session_state.selected_theme = "Dark"
                st.rerun()
        
        if st.session_state.theme_mode == "dark":
            available_themes = {k: v for k, v in THEMES.items() if v["type"] == "dark"}
        else:
            available_themes = {k: v for k, v in THEMES.items() if v["type"] == "light"}
        
        if st.session_state.selected_theme not in available_themes:
            st.session_state.selected_theme = list(available_themes.keys())[0]
        
        selected_theme_name = st.selectbox(
            f"Choose {st.session_state.theme_mode.title()} Theme:",
            list(available_themes.keys()),
            index=list(available_themes.keys()).index(st.session_state.selected_theme)
        )
        
        if selected_theme_name != st.session_state.selected_theme:
            st.session_state.selected_theme = selected_theme_name
            st.rerun()
        # --- END THEME UI ---

        st.divider()
        if st.button("Logout", type="primary"):
            logout()
    
    # --- Dashboard Routing ---
    if st.session_state.user_role == "Doctor":
        doctor_dashboard()
    elif st.session_state.user_role == "Nurse":
        nurse_dashboard()
    elif st.session_state.user_role == "Patient":
        patient_dashboard()