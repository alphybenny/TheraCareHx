import streamlit as st
from database import get_profile_by_user_id, get_all_user_data
import json
import requests
import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from datetime import datetime
import time
from PyPDF2 import PdfReader, PdfWriter
import secrets

st.set_page_config(
    page_title="TheraCare - Dashboard",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Professional CSS styling
st.markdown("""
    <style>
        /* Main page styling */
        .main {
            background-color: #1a1a1a;
        }
        
        [data-testid="stHeader"] {
            background-color: #1a1a1a;
        }
        
        /* Hide sidebar navigation */
        [data-testid="stSidebarNav"] {
            display: none;
        }
        
        /* Sidebar styling */
        [data-testid="stSidebar"] {
            background-color: #1a1a1a;
            border-right: 1px solid #333;
        }
        
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
            color: #ffffff;
            padding: 0.5rem 0;
            font-size: 1rem;
        }
        
        /* Logout button styling */
        .stButton button {
            background-color: #FF4B4B !important;
            color: white !important;
            border: none !important;
            border-radius: 4px !important;
            padding: 0.5rem 1rem !important;
            width: 100% !important;
            transition: all 0.3s ease !important;
        }
        
        .stButton button:hover {
            background-color: #FF3333 !important;
            transform: translateY(-1px) !important;
            box-shadow: 0 2px 5px rgba(255, 75, 75, 0.2) !important;
        }
        
        /* Profile box styling */
        .profile-box {
            background-color: #1a1a1a;
            border: 1px solid #333;
            border-radius: 15px;
            padding: 2rem;
            max-width: 500px;
            margin: 2rem auto;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        /* Profile picture styling */
        .profile-pic-container {
            text-align: center;
            margin-bottom: 2rem;
        }
        
        .profile-pic {
            width: 150px;
            height: 150px;
            border-radius: 50%;
            border: 3px solid #2d89ef;
            box-shadow: 0 0 15px rgba(45, 137, 239, 0.2);
            transition: all 0.3s ease;
        }
        
        .profile-pic:hover {
            transform: scale(1.02);
            box-shadow: 0 0 20px rgba(45, 137, 239, 0.3);
        }
        
        /* Profile details styling */
        .profile-details {
            background-color: #242424;
            border-radius: 10px;
            padding: 1.5rem;
            margin: 1rem 0;
        }
        
        .profile-field {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.75rem 0;
            border-bottom: 1px solid #333;
        }
        
        .profile-field:last-child {
            border-bottom: none;
        }
        
        .field-label {
            color: #888;
            font-size: 0.9rem;
        }
        
        .field-value {
            color: #fff;
            font-size: 1rem;
            font-weight: 500;
        }
        
        /* Edit profile button styling */
        .edit-profile-btn {
            background-color: #2d89ef !important;
            color: white !important;
            padding: 0.75rem 2rem !important;
            border-radius: 8px !important;
            font-weight: 500 !important;
            letter-spacing: 0.5px !important;
            transition: all 0.3s ease !important;
            width: 100% !important;
            margin-top: 1rem !important;
            cursor: pointer !important;
            border: none !important;
        }
        
        .edit-profile-btn:hover {
            background-color: #2476d3 !important;
            transform: translateY(-1px) !important;
            box-shadow: 0 4px 8px rgba(45, 137, 239, 0.2) !important;
        }
        
        /* Title styling */
        h1 {
            color: #ffffff !important;
            font-size: 2.5rem !important;
            font-weight: 600 !important;
            margin-bottom: 2rem !important;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1) !important;
        }
        
        /* Custom divider */
        .custom-divider {
            border-top: 1px solid #333;
            margin: 1rem 0;
        }
    </style>
""", unsafe_allow_html=True)

def display_profile_section():
    st.markdown('<div class="profile-box">', unsafe_allow_html=True)
    
    # Get user's profile data
    profile = get_profile_by_user_id(st.session_state.user_id)
    
    # Profile picture section
    st.markdown("""
        <div class="profile-pic-container">
            <img src="https://www.w3schools.com/howto/img_avatar.png" class="profile-pic" alt="Profile Picture">
        </div>
    """, unsafe_allow_html=True)
    
    if profile:
        profile_data = profile['profile_data']
        name_data = profile_data.get('name', [{}])[0]
        address_data = profile_data.get('address', [{}])[0]
        
        # Profile details section
        st.markdown("""
            <div class="profile-details">
                <div class="profile-field">
                    <span class="field-label">Name</span>
                    <span class="field-value">{}</span>
                </div>
                <div class="profile-field">
                    <span class="field-label">Gender</span>
                    <span class="field-value">{}</span>
                </div>
                <div class="profile-field">
                    <span class="field-label">Date of Birth</span>
                    <span class="field-value">{}</span>
                </div>
                <div class="profile-field">
                    <span class="field-label">Address</span>
                    <span class="field-value">{}</span>
                </div>
                <div class="profile-field">
                    <span class="field-label">Healthcare Provider</span>
                    <span class="field-value">{}</span>
                </div>
            </div>
        """.format(
            name_data.get('text', ''),
            profile_data.get('gender', ''),
            profile_data.get('birthDate', ''),
            address_data.get('text', ''),
            profile_data.get('managingOrganization', {}).get('display', '')
        ), unsafe_allow_html=True)
    else:
        st.markdown("""
            <div class="profile-details">
                <div class="profile-field">
                    <span class="field-label">Username</span>
                    <span class="field-value">{}</span>
                </div>
                <div class="profile-field">
                    <span class="field-label">Status</span>
                    <span class="field-value">No profile data available</span>
                </div>
            </div>
        """.format(st.session_state.username), unsafe_allow_html=True)
    
    # Edit Profile Button that links to the edit profile page
    if st.button("Edit Profile", key="edit_profile", use_container_width=True):
        st.switch_page("pages/4_EditProfile.py")
    
    st.markdown('</div>', unsafe_allow_html=True)

def show_dashboard():
    """
    Display the main dashboard with user information and actions
    """
    st.title("Dashboard")
    
    # Display user information
    st.subheader("Welcome!")
    st.write(f"Username: {st.session_state.username}")
    
    # Display Gorilla ID if available
    if st.session_state.gorilla_id:
        st.write(f"Gorilla ID: {st.session_state.gorilla_id}")
    
    # Get user's profile if it exists
    profile = get_profile_by_user_id(st.session_state.user_id)
    if profile:
        st.subheader("Your Profile")
        profile_data = profile.get("profile_data", {})
        
        # Display basic information
        if "name" in profile_data:
            name = profile_data["name"]
            st.write(f"Name: {name.get('given', '')} {name.get('family', '')}")
        
        if "gender" in profile_data:
            st.write(f"Gender: {profile_data['gender']}")
        
        if "birthDate" in profile_data:
            st.write(f"Date of Birth: {profile_data['birthDate']}")
        
        # Display address information
        if "address" in profile_data:
            address = profile_data["address"]
            st.write("Address:")
            for line in address.get("line", []):
                st.write(f"- {line}")
            st.write(f"{address.get('city', '')}, {address.get('state', '')} {address.get('postalCode', '')}")
    
    # Navigation buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Edit Profile"):
            st.session_state.page = "EditProfile"
            st.experimental_rerun()
    with col2:
        if st.button("Your Conditions"):
            st.switch_page("pages/5_YourConditions.py")
    with col3:
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.token = None
            st.session_state.username = None
            st.session_state.user_id = None
            st.session_state.gorilla_id = None
            st.experimental_rerun()

def generate_health_report(user_data):
    """
    Generate a health report using GPT-4 and convert to PDF
    """
    try:
        # Check if OpenAI API key is available
        if not os.getenv('OPENAI_API_KEY'):
            st.error("OpenAI API key is not configured. Please contact your administrator.")
            return False
        
        # Extract conditions from the response
        conditions = []
        if 'conditions' in user_data and user_data['conditions'] is not None:
            api_response = user_data['conditions'].get('api_response', [])
            if api_response is not None:
                if isinstance(api_response, list):
                    for entry in api_response:
                        if isinstance(entry, dict) and 'resource' in entry:
                            conditions.append(entry['resource'])
        
        # Filter out empty conditions and optimize the data
        optimized_conditions = []
        for condition in conditions:
            try:
                # Handle both string and dictionary formats
                if isinstance(condition, str):
                    try:
                        condition = json.loads(condition)
                    except json.JSONDecodeError:
                        # If it's not valid JSON, treat it as a simple condition name
                        if condition.strip():  # Only add if not empty
                            optimized_condition = {
                                'name': condition,
                                'onsetDate': 'Not specified',
                                'recordedDate': 'Not specified'
                            }
                            optimized_conditions.append(optimized_condition)
                        continue

                # Handle dictionary format - only extract name and dates
                condition_name = ''
                if isinstance(condition.get('code'), dict):
                    condition_name = condition['code'].get('text', '')
                elif isinstance(condition.get('code'), str):
                    condition_name = condition['code']
                
                # Only add if the condition name is not empty
                if condition_name.strip():
                    # Get recorded date from assertedDate
                    recorded_date = condition.get('assertedDate', '')
                    if recorded_date:
                        recorded_date = recorded_date.split('T')[0]
                    else:
                        recorded_date = 'Not specified'
                    
                    # Get onset date from onsetPeriod or onsetDateTime
                    onset_date = ''
                    onset_period = condition.get('onsetPeriod', {})
                    if isinstance(onset_period, dict):
                        onset_date = onset_period.get('start', '')
                    elif isinstance(onset_period, str):
                        onset_date = onset_period
                    
                    # If no onset date from onsetPeriod, try onsetDateTime
                    if not onset_date:
                        onset_date = condition.get('onsetDateTime', '')
                    
                    if onset_date:
                        onset_date = onset_date.split('T')[0]
                    else:
                        onset_date = 'Not specified'
                    
                    optimized_condition = {
                        'name': condition_name,
                        'onsetDate': onset_date,
                        'recordedDate': recorded_date
                    }
                    optimized_conditions.append(optimized_condition)
            except Exception as e:
                st.warning(f"Warning: Could not process condition: {str(e)}")
                continue

        total_conditions = len(optimized_conditions)
        
        # Extract and optimize family history
        optimized_family_history = []
        if 'family_history' in user_data and user_data['family_history'] is not None:
            family_history = user_data['family_history']
            if isinstance(family_history, dict) and 'api_response' in family_history:
                entries = family_history['api_response'].get('entry', [])
                for entry in entries:
                    if isinstance(entry, dict) and 'resource' in entry:
                        resource = entry['resource']
                        # Get relationship
                        relationship = ''
                        if 'relationship' in resource:
                            rel_data = resource['relationship']
                            if isinstance(rel_data, dict):
                                relationship = rel_data.get('text', '')
                                if not relationship and 'coding' in rel_data:
                                    for coding in rel_data.get('coding', []):
                                        if 'display' in coding:
                                            relationship = coding['display']
                                            break
                        
                        # Get conditions
                        conditions = []
                        if 'condition' in resource:
                            for cond in resource.get('condition', []):
                                if isinstance(cond, dict) and 'code' in cond:
                                    code_data = cond['code']
                                    condition_name = ''
                                    if isinstance(code_data, dict):
                                        condition_name = code_data.get('text', '')
                                        if not condition_name and 'coding' in code_data:
                                            for coding in code_data.get('coding', []):
                                                if 'display' in coding:
                                                    condition_name = coding['display']
                                                    break
                                    
                                    if condition_name.strip() and condition_name.lower() != 'no known problems':
                                        condition_info = {
                                            'name': condition_name,
                                            'age_at_diagnosis': cond.get('onsetAge', {}).get('value', 'Not specified'),
                                            'is_cause_of_death': any(
                                                ext.get('url', '').endswith('cause-of-death') and ext.get('valueBoolean', False)
                                                for ext in cond.get('extension', [])
                                            )
                                        }
                                        conditions.append(condition_info)
                        
                        # Only add if there are conditions or if it's a significant family member
                        if conditions or relationship.strip():
                            family_member = {
                                'relationship': relationship or 'Not specified',
                                'conditions': conditions,
                                'born_date': resource.get('bornDate', 'Not specified'),
                                'gender': resource.get('gender', 'Not specified')
                            }
                            optimized_family_history.append(family_member)
        
        # If no data found, show a message
        if total_conditions == 0 and not optimized_family_history:
            st.info("No medical conditions or family history found in the records.")
            return False

        # Get user information
        user_info = user_data.get('user_info', {})
        profile = user_data.get('profile', {})
        profile_data = profile.get('profile_data', {})
        
        # Extract user details
        name = 'Not specified'
        if 'name' in profile_data:
            name_parts = profile_data['name']
            if isinstance(name_parts, list) and len(name_parts) > 0:
                name_parts = name_parts[0]
            if isinstance(name_parts, dict):
                given = name_parts.get('given', [])
                family = name_parts.get('family', '')
                name = f"{' '.join(given)} {family}".strip()
        
        gender = profile_data.get('gender', 'Not specified')
        birth_date = profile_data.get('birthDate', 'Not specified')
        email = user_info.get('email', 'Not specified')
        
        # Prepare the prompt for GPT-4
        prompt = f"""
        Please analyze this health data and create a simple, list-based health report.
        IMPORTANT: You must include ALL conditions and family history entries. Do not skip any.
        
        Patient Information:
        - Name: {name}
        - Gender: {gender}
        - Date of Birth: {birth_date}
        - Email: {email}
        
        Medical Conditions (Total: {total_conditions}):
        {json.dumps(optimized_conditions, indent=2)}
        
        Family History:
        {json.dumps(optimized_family_history, indent=2)}
        
        Please format the report in the following structure:

        PATIENT INFORMATION
        Name: {name}
        Gender: {gender}
        Date of Birth: {birth_date}
        Email: {email}

        YOUR CONDITIONS (Total: {total_conditions})
        [List ALL conditions in numerical order, starting from 1]
        1. [Condition Name]
           - Onset Date: [date]
           - Recorded Date: [date]

        2. [Next Condition Name]
           - Onset Date: [date]
           - Recorded Date: [date]

        [Continue listing ALL conditions...]

        FAMILY HISTORY
        [List ALL family members in numerical order, starting from 1]
        1. [Family Member - e.g., Grandfather]
           - Conditions: [list all conditions]
           - Age at Diagnosis: [age]
           - Current Status: [status]

        2. [Next Family Member - e.g., Father]
           - Conditions: [list all conditions]
           - Age at Diagnosis: [age]
           - Current Status: [status]

        [Continue listing ALL family members...]

        IMPORTANT INSTRUCTIONS:
        1. Do not skip any conditions or family members
        2. List everything in the exact order provided
        3. Include all details for each entry
        4. Maintain consistent formatting throughout
        5. Verify the total count matches the input data
        """
        
        # Add retry logic for API calls
        max_retries = 3
        retry_delay = 5  # seconds
        timeout = 120  # seconds
        
        for attempt in range(max_retries):
            try:
                # Call GPT-4 API with increased timeout
                response = requests.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "gpt-4o-mini",
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.7
                    },
                    timeout=timeout
                )
                
                if response.status_code == 200:
                    try:
                        report_content = response.json()['choices'][0]['message']['content']
                        
                        # Create PDF
                        doc = SimpleDocTemplate(
                            f"health_report_{st.session_state.username}.pdf",
                            pagesize=letter,
                            rightMargin=72,
                            leftMargin=72,
                            topMargin=72,
                            bottomMargin=72
                        )
                        
                        # Custom styles
                        styles = getSampleStyleSheet()
                        
                        # Title style
                        title_style = ParagraphStyle(
                            'CustomTitle',
                            parent=styles['Heading1'],
                            fontSize=24,
                            textColor=colors.HexColor('#2d89ef'),
                            spaceAfter=30,
                            alignment=1  # Center alignment
                        )
                        
                        # Subtitle style
                        subtitle_style = ParagraphStyle(
                            'CustomSubtitle',
                            parent=styles['Normal'],
                            fontSize=12,
                            textColor=colors.HexColor('#666666'),
                            spaceAfter=20,
                            alignment=1
                        )
                        
                        # Section header style
                        section_style = ParagraphStyle(
                            'CustomSection',
                            parent=styles['Heading2'],
                            fontSize=16,
                            textColor=colors.HexColor('#2d89ef'),
                            spaceAfter=15,
                            spaceBefore=20,
                            leftIndent=0
                        )
                        
                        # Patient info style
                        info_style = ParagraphStyle(
                            'CustomInfo',
                            parent=styles['Normal'],
                            fontSize=12,
                            spaceAfter=10,
                            leftIndent=20
                        )
                        
                        # Condition style
                        condition_style = ParagraphStyle(
                            'CustomCondition',
                            parent=styles['Normal'],
                            fontSize=12,
                            spaceAfter=10,
                            leftIndent=20
                        )
                        
                        # Detail style
                        detail_style = ParagraphStyle(
                            'CustomDetail',
                            parent=styles['Normal'],
                            fontSize=11,
                            spaceAfter=5,
                            leftIndent=40,
                            textColor=colors.HexColor('#666666')
                        )
                        
                        # Build PDF content
                        story = []
                        
                        # Add title and subtitle
                        story.append(Paragraph("HEALTH SUMMARY REPORT", title_style))
                        story.append(Paragraph(f"Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", subtitle_style))
                        story.append(Spacer(1, 20))
                        
                        # Add patient information section
                        story.append(Paragraph("PATIENT INFORMATION", section_style))
                        story.append(Paragraph(f"<b>Name:</b> {name}", info_style))
                        story.append(Paragraph(f"<b>Gender:</b> {gender}", info_style))
                        story.append(Paragraph(f"<b>Date of Birth:</b> {birth_date}", info_style))
                        story.append(Paragraph(f"<b>Email:</b> {email}", info_style))
                        story.append(Spacer(1, 20))
                        
                        # Add conditions section
                        story.append(Paragraph(f"YOUR CONDITIONS ({total_conditions} Total)", section_style))
                        
                        # Process content
                        current_section = None
                        for line in report_content.split('\n'):
                            line = line.strip()
                            if not line:
                                continue
                            
                            # Skip duplicate patient information
                            if line.startswith("## PATIENT INFORMATION") or line.startswith("PATIENT INFORMATION-"):
                                continue
                            
                            # Skip markdown headers
                            if line.startswith("#") or line.startswith("##"):
                                continue
                            
                            # Check for main sections
                            if line in ['YOUR CONDITIONS', 'FAMILY HISTORY']:
                                current_section = line
                                if line == 'FAMILY HISTORY':
                                    story.append(Spacer(1, 20))
                                    story.append(Paragraph(line, section_style))
                                continue
                            
                            # Check for condition/family member numbers
                            if line[0].isdigit() and line[1] == '.':
                                # Remove markdown formatting
                                line = line.replace('**', '')
                                story.append(Paragraph(line, condition_style))
                            # Check for details (starting with -)
                            elif line.startswith('-'):
                                # Remove markdown formatting and ensure proper spacing
                                line = line.replace('**', '').replace('-', '•')
                                story.append(Paragraph(line, detail_style))
                            else:
                                # Remove markdown formatting
                                line = line.replace('**', '')
                                story.append(Paragraph(line, detail_style))
                            
                            story.append(Spacer(1, 5))
                        
                        # Add footer
                        story.append(Spacer(1, 30))
                        story.append(Paragraph("This report was generated by TheraCare", subtitle_style))
                        story.append(Paragraph("For any questions or concerns, please contact your healthcare provider", subtitle_style))
                        
                        # Generate PDF
                        doc.build(story)
                        
                        # Generate password using username and date of birth
                        username = st.session_state.username
                        dob = user_data.get('profile', {}).get('profile_data', {}).get('birthDate', '')
                        # Format: username@YYYY (year from DOB)
                        password = f"{username}@{dob.split('-')[0]}" if dob else f"{username}@2024"
                        
                        # Encrypt the PDF
                        pdf_reader = PdfReader(f"health_report_{st.session_state.username}.pdf")
                        pdf_writer = PdfWriter()
                        
                        # Add all pages to the writer
                        for page in pdf_reader.pages:
                            pdf_writer.add_page(page)
                        
                        # Add password protection
                        pdf_writer.encrypt(password)
                        
                        # Save the encrypted PDF
                        encrypted_pdf_path = f"health_report_{st.session_state.username}_encrypted.pdf"
                        with open(encrypted_pdf_path, "wb") as output_file:
                            pdf_writer.write(output_file)
                        
                        # Remove the original unencrypted PDF
                        os.remove(f"health_report_{st.session_state.username}.pdf")
                        
                        # Store the password in session state
                        st.session_state.pdf_password = password
                        
                        return True
                        
                    except Exception as e:
                        st.error(f"Error processing GPT response: {str(e)}")
                        return False
                        
                else:
                    error_msg = f"API Error: {response.status_code}"
                    try:
                        error_details = response.json()
                        error_msg += f" - {error_details.get('error', {}).get('message', 'Unknown error')}"
                    except:
                        error_msg += " - Could not parse error details"
                    
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        continue
                    else:
                        st.error(error_msg)
                        return False
                        
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                else:
                    st.error("Request timed out after multiple attempts. Please try again later.")
                    return False
                    
    except requests.exceptions.RequestException as e:
        st.error(f"Network error: {str(e)}")
        return False
    except Exception as e:
        st.error(f"Unexpected error: {str(e)}")
        return False

def main():
    if not st.session_state.get("logged_in"):
        st.switch_page("pages/1_Login.py")
        return

    # Sidebar with welcome message and navigation
    with st.sidebar:
        st.write(f"Welcome, {st.session_state.username}!")
        st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
        
        # Navigation buttons in sidebar
        if st.button("Edit Profile", key="sidebar_edit_profile", use_container_width=True):
            st.switch_page("pages/4_EditProfile.py")
        
        if st.button("Your Conditions", key="sidebar_conditions", use_container_width=True):
            st.switch_page("pages/5_YourConditions.py")
        
        if st.button("Family History", key="sidebar_family_history", use_container_width=True):
            st.switch_page("pages/6_FamilyHistory.py")
        
        st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
        
        if st.button("Logout", key="sidebar_logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.token = None
            st.session_state.username = None
            st.session_state.user_id = None
            st.session_state.gorilla_id = None
            st.switch_page("pages/1_Login.py")

    # Main content
    st.title("TheraCare Dashboard")
    
    # Create three columns and use the middle one for profile
    col1, col2, col3, col4 = st.columns([1, 2, 1, 1])
    with col2:
        display_profile_section()
        
        # Quick access buttons below profile
        st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("Edit Profile", key="main_edit_profile", use_container_width=True):
                st.switch_page("pages/4_EditProfile.py")
        with col2:
            if st.button("Your Conditions", key="main_conditions", use_container_width=True):
                st.switch_page("pages/5_YourConditions.py")
        with col3:
            if st.button("Family History", key="main_family_history", use_container_width=True):
                st.switch_page("pages/6_FamilyHistory.py")
        with col4:
            if st.button("Download Profile", key="download_profile", use_container_width=True):
                # Get all user data
                user_data = get_all_user_data(st.session_state.user_id)
                if user_data:
                    # Convert to JSON string
                    json_str = json.dumps(user_data, indent=2)
                    # Create download button
                    st.download_button(
                        label="Download Profile Data",
                        data=json_str,
                        file_name=f"profile_data_{st.session_state.username}.json",
                        mime="application/json"
                    )
                else:
                    st.error("Failed to generate profile data")
            
            # Add new Health Report button
            if st.button("Download Health Report", key="download_health_report", use_container_width=True):
                # Get all user data
                user_data = get_all_user_data(st.session_state.user_id)
                if user_data:
                    # Show loading message
                    with st.spinner("Generating your health report..."):
                        # Generate PDF report
                        if generate_health_report(user_data):
                            # Read the generated PDF
                            with open(f"health_report_{st.session_state.username}_encrypted.pdf", "rb") as f:
                                pdf_data = f.read()
                            
                            # Create download button for the PDF
                            st.download_button(
                                label="Download Health Report",
                                data=pdf_data,
                                file_name=f"health_report_{st.session_state.username}.pdf",
                                mime="application/pdf"
                            )
                            
                            # Display the password to the user only once
                            if 'pdf_password_displayed' not in st.session_state:
                                st.info(f"Your PDF password is: {st.session_state.pdf_password}")
                                st.warning("Please save this password securely. You will need it to open the PDF.")
                                st.session_state.pdf_password_displayed = True
                            
                            # Clean up the temporary file
                            os.remove(f"health_report_{st.session_state.username}_encrypted.pdf")
                else:
                    st.error("Failed to generate health report. Please try again later.")

if __name__ == "__main__":
    main() 