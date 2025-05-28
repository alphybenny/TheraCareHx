import streamlit as st
import time
from datetime import datetime
import requests
import os
from dotenv import load_dotenv
import json
from database import save_profile, get_profile_by_user_id

# Load environment variables
load_dotenv()
API_BASE_URL = os.getenv('API_BASE_URL')

st.set_page_config(
    page_title="TheraCare - Edit Profile",
    page_icon="🏥",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Enhanced styling
st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {
            display: none;
        }
        
        .stButton button {
            width: 100%;
        }
        
        .go-back-btn {
            position: absolute;
            top: 1rem;
            left: 1rem;
            color: #888;
            text-decoration: none;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .go-back-btn:hover {
            color: #2d89ef;
        }

        /* Option cards styling */
        .option-container {
            display: flex;
            gap: 1rem;
            margin: 2rem 0;
        }
        
        .option-card {
            background-color: #1a1a1a;
            border: 1px solid #333;
            border-radius: 10px;
            padding: 1.5rem;
            cursor: pointer;
            transition: all 0.3s ease;
            flex: 1;
            text-align: center;
        }
        
        .option-card:hover {
            border-color: #2d89ef;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(45, 137, 239, 0.1);
        }
        
        .option-card.selected {
            border-color: #2d89ef;
            background-color: #1e2f3e;
        }
        
        .option-icon {
            font-size: 2rem;
            margin-bottom: 1rem;
            color: #2d89ef;
        }
        
        .option-title {
            font-size: 1.2rem;
            font-weight: 600;
            color: #fff;
            margin-bottom: 0.5rem;
        }
        
        .option-description {
            color: #888;
            font-size: 0.9rem;
        }

        /* Form styling */
        .form-container {
            background-color: #1a1a1a;
            border: 1px solid #333;
            border-radius: 10px;
            padding: 2rem;
            margin-top: 2rem;
        }

        /* Import section styling */
        .import-container {
            background-color: #1a1a1a;
            border: 1px solid #333;
            border-radius: 10px;
            padding: 2rem;
            margin-top: 2rem;
            text-align: center;
        }

        /* Step indicator styling */
        .step-container {
            margin-bottom: 2rem;
            padding: 1rem;
            background-color: #1a1a1a;
            border-radius: 8px;
            border: 1px solid #333;
        }
        
        .step-title {
            color: #2d89ef;
            font-size: 1.1rem;
            margin-bottom: 0.5rem;
            font-weight: 500;
        }
        
        .step-description {
            color: #888;
            font-size: 0.9rem;
            margin-bottom: 1rem;
        }
        
        /* Result container styling */
        .result-container {
            margin-top: 1rem;
            padding: 1rem;
            background-color: #1e2f3e;
            border-radius: 8px;
            border: 1px solid #2d89ef;
        }
        
        .patient-info {
            margin-top: 1rem;
            padding: 1rem;
            background-color: #242424;
            border-radius: 8px;
        }
        
        .info-row {
            display: flex;
            justify-content: space-between;
            padding: 0.5rem 0;
            border-bottom: 1px solid #333;
        }
        
        .info-label {
            color: #888;
        }
        
        .info-value {
            color: #fff;
            font-weight: 500;
        }
    </style>
""", unsafe_allow_html=True)

def search_patient(given_name, family_name, dob):
    """
    Search for a patient using the health system API
    """
    try:
        # First make the search API call
        search_url = f"{API_BASE_URL}/search"
        search_params = {
            "given": given_name,
            "family": family_name,
            "birthdate": dob.strftime("%Y-%m-%d")
        }
        
        print(f"\nMaking search API request to: {search_url}")
        print(f"With parameters: {search_params}")
        
        search_response = requests.get(search_url, params=search_params)
        print(f"Search API Response Status Code: {search_response.status_code}")
        print(f"Search API Response Content: {search_response.text}")
        
        if search_response.status_code == 200:
            search_data = search_response.json()
            # Check if we got patients in the response
            if search_data.get("count", 0) > 0 and search_data.get("patients"):
                # Get the first patient from the results
                patient = search_data["patients"][0]
                patient_id = patient.get("id")
                
                if patient_id:
                    # Store the gorilla_id in session state
                    st.session_state.gorilla_id = patient_id
                    
                    # Now fetch the complete patient details
                    details_url = f"{API_BASE_URL}/patient/{patient_id}"
                    print(f"\nFetching patient details from: {details_url}")
                    
                    details_response = requests.get(details_url)
                    print(f"Details API Response Status Code: {details_response.status_code}")
                    print(f"Details API Response Content: {details_response.text}")
                    
                    if details_response.status_code == 200:
                        return details_response.json()
        
        return None
            
    except Exception as e:
        print(f"\nError during API call: {str(e)}")
        st.error(f"Error during search: {str(e)}")
        return None

def get_patient_details(patient_id):
    """
    Fetch detailed patient information from the API
    """
    try:
        details_url = f"{API_BASE_URL}/patient/{patient_id}"
        print(f"\nFetching patient details from: {details_url}")
        
        response = requests.get(details_url)
        print(f"API Response Status Code: {response.status_code}")
        
        if response.status_code == 200:
            return response.json()
        return None
        
    except Exception as e:
        print(f"\nError fetching patient details: {str(e)}")
        st.error(f"Error fetching details: {str(e)}")
        return None

def show_patient_details_form(patient_data):
    """
    Display and allow editing of patient details
    """
    st.markdown("""
        <div class="form-container">
            <h3>Patient Details</h3>
            <p class="subtitle">Review and update your information</p>
        </div>
    """, unsafe_allow_html=True)

    # Basic Information
    st.subheader("Basic Information")
    col1, col2 = st.columns(2)
    
    # Extract name components
    name_data = patient_data.get("name", [{}])[0]
    given_name = name_data.get("given", [""])[0] if name_data.get("given") else ""
    family_name = name_data.get("family", "")
    
    with col1:
        given_name = st.text_input("Given Name", value=given_name)
        gender = st.selectbox("Gender", 
                            options=["male", "female", "other"],
                            index=["male", "female", "other"].index(patient_data.get("gender", "other")))
    with col2:
        family_name = st.text_input("Family Name", value=family_name)
        birth_date = st.date_input("Date of Birth", 
                                 value=datetime.strptime(patient_data.get("birthDate", "1900-01-01"), "%Y-%m-%d"))

    # Address Information
    st.subheader("Address")
    address_data = patient_data.get("address", [{}])[0] if patient_data.get("address") else {}
    
    # Street Address (can have multiple lines)
    address_lines = address_data.get("line", ["", ""])
    address_line1 = st.text_input("Address Line 1", value=address_lines[0] if len(address_lines) > 0 else "")
    address_line2 = st.text_input("Address Line 2", value=address_lines[1] if len(address_lines) > 1 else "")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        city = st.text_input("City", value=address_data.get("city", ""))
    with col2:
        state = st.text_input("State", value=address_data.get("state", ""))
    with col3:
        postal_code = st.text_input("Postal Code", value=address_data.get("postalCode", ""))

    # Healthcare Provider (read-only)
    st.subheader("Healthcare Provider")
    org_data = patient_data.get("managingOrganization", {})
    healthcare_provider = st.text_input(
        "Healthcare Provider",
        value=org_data.get("display", ""),
        disabled=True,
        help="Your primary healthcare provider"
    )

    # Meta Information in expander
    with st.expander("Record Information"):
        meta = patient_data.get("meta", {})
        st.text_input(
            "Last Updated",
            value=meta.get("lastUpdated", ""),
            disabled=True
        )
        st.text_input(
            "Version ID",
            value=meta.get("versionId", ""),
            disabled=True
        )

    # Action Buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Save Changes", type="primary", key="save_imported_changes"):
            # Create a copy of the original patient data
            updated_profile = patient_data.copy()
            
            # Update only the fields that were edited
            updated_profile["name"] = [{
                "given": [given_name],
                "family": family_name,
                "text": f"{given_name} {family_name}",
                "use": "usual"
            }]
            updated_profile["gender"] = gender
            updated_profile["birthDate"] = birth_date.strftime("%Y-%m-%d")
            
            # Update address while preserving any additional address fields
            updated_profile["address"] = [{
                **address_data,  # Preserve original address fields
                "line": [address_line1, address_line2] if address_line2 else [address_line1],
                "city": city,
                "state": state,
                "postalCode": postal_code,
                "text": f"{address_line1}, {city}, {state} {postal_code}"
            }]
            
            # Save to database
            try:
                profile_id = save_profile(
                    user_id=st.session_state.user_id,
                    gorilla_id=patient_data.get("id"),
                    profile_data=updated_profile
                )
                
                if profile_id:
                    st.success("Profile updated successfully!")
                    time.sleep(1)
                    st.switch_page("pages/2_Dashboard.py")
                else:
                    st.error("Failed to save profile. Please try again.")
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
    with col2:
        if st.button("Cancel", key="cancel_imported_changes"):
            st.switch_page("pages/2_Dashboard.py")

def show_import_section():
    st.markdown('<div class="import-container">', unsafe_allow_html=True)
    
    # Step 1: Patient Identification
    if st.session_state.import_step == 1:
        st.markdown("""
            <div class="step-container">
                <div class="step-title">Step 1: Patient Identification</div>
                <div class="step-description">Please enter your details to find your health record</div>
            </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            given_name = st.text_input("Given Name", placeholder="Enter your given name")
        with col2:
            family_name = st.text_input("Family Name", placeholder="Enter your family name")
        
        dob = st.date_input("Date of Birth", 
                           min_value=datetime(1900, 1, 1),
                           max_value=datetime.now())
        
        if st.button("Find My Health Record", type="primary", key="find_health_record"):
            if given_name and family_name and dob:
                with st.spinner("Searching for your health record..."):
                    # Get patient details directly
                    patient_data = search_patient(given_name, family_name, dob)
                    
                    if patient_data:
                        # Store the complete patient details in session state
                        st.session_state.patient_details = patient_data
                        st.session_state.search_done = True
                        
                        # Extract name from the response
                        name = patient_data.get("name", [{}])[0].get("text", "")
                        
                        # Display the found patient details
                        st.markdown("""
                            <div class="result-container">
                                <h4>Patient Found ✓</h4>
                                <div class="patient-info">
                                    <div class="info-row">
                                        <span class="info-label">Name:</span>
                                        <span class="info-value">{}</span>
                                    </div>
                                    <div class="info-row">
                                        <span class="info-label">Date of Birth:</span>
                                        <span class="info-value">{}</span>
                                    </div>
                                    <div class="info-row">
                                        <span class="info-label">Patient ID:</span>
                                        <span class="info-value">{}</span>
                                    </div>
                                </div>
                            </div>
                        """.format(
                            name,
                            patient_data.get("birthDate", ""),
                            patient_data.get("id", "")
                        ), unsafe_allow_html=True)
                    else:
                        st.error("No matching patient record found. Please check your details and try again.")
            else:
                st.error("Please fill in all required fields")
        
        # Only show the continue button if search was successful
        if st.session_state.get("search_done", False):
            continue_col1, continue_col2 = st.columns([3, 1])
            with continue_col2:
                if st.button("Continue →", key="continue_to_details"):
                    st.session_state.import_step = 2
                    st.rerun()

    # Step 2: Show and Edit Patient Details
    elif st.session_state.import_step == 2:
        if st.session_state.patient_details:
            show_patient_details_form(st.session_state.patient_details)
        else:
            st.error("Patient details not found. Please go back and try again.")
            if st.button("Go Back", key="go_back_to_search"):
                st.session_state.import_step = 1
                st.session_state.search_done = False
                st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

def show_manual_form():
    st.markdown('<div class="form-container">', unsafe_allow_html=True)
    st.write("📝 Manual Profile Information")
    
    # Get existing profile if any
    existing_profile = get_profile_by_user_id(st.session_state.user_id)
    profile_data = existing_profile['profile_data'] if existing_profile else None
    
    # Basic Information
    st.subheader("Basic Information")
    col1, col2 = st.columns(2)
    
    # Extract name components from existing profile or set defaults
    name_data = profile_data.get("name", [{}])[0] if profile_data else {}
    given_name = name_data.get("given", [""])[0] if name_data.get("given") else ""
    family_name = name_data.get("family", "") if name_data else ""
    
    with col1:
        given_name = st.text_input("Given Name", value=given_name, placeholder="Enter your given name")
        gender = st.selectbox(
            "Gender", 
            options=["male", "female", "other"],
            index=["male", "female", "other"].index(profile_data.get("gender", "other")) if profile_data else 0
        )
    with col2:
        family_name = st.text_input("Family Name", value=family_name, placeholder="Enter your family name")
        birth_date = st.date_input(
            "Date of Birth", 
            value=datetime.strptime(profile_data.get("birthDate", "1900-01-01"), "%Y-%m-%d") if profile_data else datetime.now()
        )

    # Address Information
    st.subheader("Address")
    address_data = profile_data.get("address", [{}])[0] if profile_data else {}
    
    # Street Address (can have multiple lines)
    address_lines = address_data.get("line", ["", ""])
    address_line1 = st.text_input("Address Line 1", value=address_lines[0] if len(address_lines) > 0 else "")
    address_line2 = st.text_input("Address Line 2", value=address_lines[1] if len(address_lines) > 1 else "")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        city = st.text_input("City", value=address_data.get("city", ""))
    with col2:
        state = st.text_input("State", value=address_data.get("state", ""))
    with col3:
        postal_code = st.text_input("Postal Code", value=address_data.get("postalCode", ""))

    # Healthcare Provider (read-only)
    st.subheader("Healthcare Provider")
    org_data = profile_data.get("managingOrganization", {}) if profile_data else {}
    healthcare_provider = st.text_input(
        "Healthcare Provider",
        value=org_data.get("display", ""),
        disabled=True,
        help="Your primary healthcare provider"
    )

    # Action buttons for manual form
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Save Changes", type="primary", key="save_manual_changes"):
            if not all([given_name, family_name, birth_date, gender, address_line1, city, state, postal_code]):
                st.error("Please fill in all required fields")
                return

            # Create or update profile data
            if profile_data:
                # Update existing profile
                updated_profile = profile_data.copy()
            else:
                # Create new profile
                updated_profile = {
                    "resourceType": "Patient",
                    "meta": {
                        "lastUpdated": datetime.now().isoformat(),
                        "versionId": "1"
                    }
                }

            # Update the fields
            updated_profile["name"] = [{
                "given": [given_name],
                "family": family_name,
                "text": f"{given_name} {family_name}",
                "use": "usual"
            }]
            updated_profile["gender"] = gender
            updated_profile["birthDate"] = birth_date.strftime("%Y-%m-%d")
            updated_profile["address"] = [{
                "line": [address_line1, address_line2] if address_line2 else [address_line1],
                "city": city,
                "state": state,
                "postalCode": postal_code,
                "text": f"{address_line1}, {city}, {state} {postal_code}"
            }]
            
            # Save to database
            try:
                profile_id = save_profile(
                    user_id=st.session_state.user_id,
                    gorilla_id=None,  # No gorilla ID for manual profiles
                    profile_data=updated_profile
                )
                
                if profile_id:
                    st.success("Profile updated successfully!")
                    time.sleep(1)
                    st.switch_page("pages/2_Dashboard.py")
                else:
                    st.error("Failed to save profile. Please try again.")
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
    with col2:
        if st.button("Cancel", key="cancel_manual_changes"):
            st.switch_page("pages/2_Dashboard.py")
    
    st.markdown("</div>", unsafe_allow_html=True)

def main():
    if not st.session_state.get("logged_in"):
        st.switch_page("pages/1_Login.py")
        return

    # Initialize session state variables
    if "current_method" not in st.session_state:
        st.session_state.current_method = None
    if "import_step" not in st.session_state:
        st.session_state.import_step = 1
    if "patient_details" not in st.session_state:
        st.session_state.patient_details = None
    if "search_done" not in st.session_state:
        st.session_state.search_done = False

    # Back button
    if st.button("← Back to Dashboard", key="back_to_dashboard"):
        st.switch_page("pages/2_Dashboard.py")

    st.title("Edit Profile")
    st.write("Choose how you would like to update your profile")

    # Profile method selection
    method = st.radio(
        "Select profile update method:",
        ["Import from Central Health System", "Fill Out Manually"],
        horizontal=True,
        label_visibility="collapsed"
    )

    # Reset session state when switching methods
    if st.session_state.current_method != method:
        st.session_state.import_step = 1
        st.session_state.patient_details = None
        st.session_state.search_done = False
        st.session_state.current_method = method

    # Show appropriate form based on selection
    if method == "Import from Central Health System":
        show_import_section()
    else:
        show_manual_form()

if __name__ == "__main__":
    main() 