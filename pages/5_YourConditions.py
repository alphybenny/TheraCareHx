import streamlit as st
import requests
import os
import json
from dotenv import load_dotenv
from database import get_profile_by_user_id, save_conditions, get_conditions_by_user_id, check_and_init_db, check_duplicate_condition
from streamlit_mic_recorder import mic_recorder
import whisper
import tempfile
import openai
from datetime import datetime

# Load environment variables
load_dotenv()
API_BASE_URL = os.getenv('API_BASE_URL')
TOKENIZE_API_URL = f"{API_BASE_URL}/tokenize-medical"
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Ensure FFmpeg is available to Whisper
os.environ["PATH"] += os.pathsep + r"C:\Program Files\ffmpeg-master-latest-win64-gpl-shared\ffmpeg-master-latest-win64-gpl-shared\bin"

# Initialize database if needed
check_and_init_db()

st.set_page_config(
    page_title="TheraCare - Your Conditions",
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
        
        .condition-card {
            background-color: #1a1a1a;
            border: 1px solid #333;
            border-radius: 10px;
            padding: 1.5rem;
            margin-bottom: 1rem;
        }
        
        .condition-title {
            font-size: 1.2rem;
            font-weight: 600;
            color: #fff;
            margin-bottom: 0.5rem;
        }
        
        .condition-date {
            color: #888;
            font-size: 0.9rem;
            margin-bottom: 0.5rem;
        }
        
        .condition-category {
            color: #ccc;
            margin-bottom: 0.5rem;
        }
        
        .condition-onset {
            color: #ccc;
            margin-bottom: 0.5rem;
        }
        
        .condition-status {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 15px;
            font-size: 0.9rem;
            font-weight: 500;
            margin-top: 0.5rem;
        }
        
        .status-active {
            background-color: #2d89ef;
            color: white;
        }
        
        .status-inactive {
            background-color: #333;
            color: #888;
        }
    </style>
""", unsafe_allow_html=True)

def get_conditions(gorilla_id):
    """
    Fetch conditions for a patient from the API
    """
    try:
        conditions_url = f"{API_BASE_URL}/conditions/{gorilla_id}"
        response = requests.get(conditions_url)
        
        if response.status_code == 200:
            data = response.json()
            # Check if we have an entry array in the response
            if isinstance(data, dict) and 'entry' in data:
                return data['entry']
            return None
        return None
    except Exception as e:
        st.error(f"Error fetching conditions: {str(e)}")
        return None

def show_imported_conditions():
    """
    Display conditions imported from the central health system
    """
    # Get Gorilla ID from profile if it exists
    profile = get_profile_by_user_id(st.session_state.user_id)
    if profile and profile.get('gorilla_id'):
        st.session_state.gorilla_id = profile['gorilla_id']
    
    # Display Gorilla ID if available
    if st.session_state.gorilla_id:
        st.markdown(f"""
            <div style="background-color: #1a1a1a; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
                <span style="color: #888;">Gorilla ID:</span>
                <span style="color: #2d89ef; font-weight: 500;">{st.session_state.gorilla_id}</span>
            </div>
        """, unsafe_allow_html=True)
        
        # Get conditions from API
        conditions = get_conditions(st.session_state.gorilla_id)
        
        if conditions and isinstance(conditions, list):
            # Organize conditions by status
            active_conditions = []
            inactive_conditions = []
            unknown_conditions = []
            
            for entry in conditions:
                condition = entry.get('resource', {})
                if not condition:
                    continue
                
                # Extract condition details
                code = condition.get('code', {})
                condition_name = code.get('text', '')
                if not condition_name and 'coding' in code:
                    coding = code.get('coding', [{}])[0]
                    condition_name = coding.get('display', 'Unknown Condition')
                
                recorded_date = condition.get('assertedDate', '')
                if recorded_date:
                    recorded_date = recorded_date.split('T')[0]
                
                # Extract clinical status properly
                clinical_status = 'unknown'
                clinical_status_obj = condition.get('clinicalStatus', {})
                if isinstance(clinical_status_obj, dict):
                    coding = clinical_status_obj.get('coding', [{}])[0]
                    if isinstance(coding, dict):
                        clinical_status = coding.get('code', 'unknown')
                elif isinstance(clinical_status_obj, str):
                    clinical_status = clinical_status_obj.lower()
                
                # Get onset date if available
                onset_period = condition.get('onsetPeriod', {})
                onset_date = onset_period.get('start', '') if onset_period else ''
                if onset_date:
                    onset_date = onset_date.split('T')[0]
                
                # Get category if available
                category = condition.get('category', [{}])[0].get('coding', [{}])[0].get('display', '')
                
                condition_data = {
                    'name': condition_name,
                    'recorded_date': recorded_date,
                    'status': clinical_status,
                    'category': category,
                    'onset_date': onset_date
                }
                
                if clinical_status == 'active':
                    active_conditions.append(condition_data)
                elif clinical_status == 'inactive':
                    inactive_conditions.append(condition_data)
                else:
                    unknown_conditions.append(condition_data)
            
            # Year filter
            all_years = sorted(set(
                condition['recorded_date'].split('-')[0] 
                for condition in active_conditions + inactive_conditions + unknown_conditions 
                if condition['recorded_date']
            ), reverse=True)
            
            selected_year = st.selectbox(
                "Filter by Year",
                ["All Years"] + all_years,
                key="year_filter"
            )
            
            # Filter conditions by year if selected
            def filter_by_year(conditions_list):
                if selected_year == "All Years":
                    return conditions_list
                return [
                    condition for condition in conditions_list 
                    if condition['recorded_date'] and condition['recorded_date'].startswith(selected_year)
                ]
            
            active_conditions = filter_by_year(active_conditions)
            inactive_conditions = filter_by_year(inactive_conditions)
            unknown_conditions = filter_by_year(unknown_conditions)
            
            # Display conditions in expanders by status
            with st.expander(f"Active Conditions ({len(active_conditions)})", expanded=True):
                for condition in active_conditions:
                    display_condition_card(condition)
            
            with st.expander(f"Inactive Conditions ({len(inactive_conditions)})"):
                for condition in inactive_conditions:
                    display_condition_card(condition)
            
            with st.expander(f"Unknown Status Conditions ({len(unknown_conditions)})"):
                for condition in unknown_conditions:
                    display_condition_card(condition)
            
            # Add save button with duplicate checking
            if st.button("Save Conditions to Database", type="primary"):
                with st.spinner("Saving conditions..."):
                    # Check for duplicates
                    duplicates = []
                    non_duplicates = []
                    for condition in conditions:
                        if check_duplicate_condition(st.session_state.user_id, condition):
                            duplicates.append(condition)
                        else:
                            non_duplicates.append(condition)
                    
                    if duplicates:
                        st.warning(f"Found {len(duplicates)} duplicate conditions. They will not be added again.")
                    
                    if non_duplicates:
                        if save_conditions(st.session_state.user_id, st.session_state.gorilla_id, non_duplicates):
                            st.success("Successfully saved new conditions to your profile!")
                        else:
                            st.error("Failed to save conditions. Please try again.")
                    else:
                        st.info("No new conditions to save.")
        else:
            st.info("No conditions found in your health record.")
    else:
        st.info("Your profile was created manually. To view your conditions, please import your profile from the central health system.")
        if st.button("Import Profile"):
            st.switch_page("pages/4_EditProfile.py")

def display_condition_card(condition):
    """
    Display a single condition card
    """
    with st.container():
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"**{condition['name']}**")
            st.caption(condition['recorded_date'])
            st.text(f"Category: {condition['category']}")
            if condition['onset_date']:
                st.text(f"Onset Date: {condition['onset_date']}")
            
            # Extract and display text/description
            if condition.get('text'):
                # Remove HTML tags and xmlns
                import re
                clean_text = re.sub('<[^<]+?>', '', condition['text'])
                clean_text = re.sub('xmlns="[^"]+"', '', clean_text)
                clean_text = clean_text.strip()
                if clean_text:
                    st.text(f"Description: {clean_text}")
        
        with col2:
            status_color = "#2d89ef" if condition['status'] == 'active' else "#333"
            status_text = condition['status'].capitalize()
            st.markdown(f"""
                <div style="
                    background-color: {status_color};
                    color: white;
                    padding: 0.25rem 0.75rem;
                    border-radius: 15px;
                    font-size: 0.9rem;
                    font-weight: 500;
                    text-align: center;
                    display: inline-block;
                ">
                    {status_text}
                </div>
            """, unsafe_allow_html=True)
        
        st.divider()

def tokenize_medical_text(text):
    """
    Call the tokenization API to get medical codes and information
    """
    try:
        response = requests.get(f"{TOKENIZE_API_URL}?text={text}")
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Error tokenizing text: {str(e)}")
        return None

def process_transcription_with_gpt(transcription):
    """
    Process the transcription with GPT-4o-mini to extract structured data
    """
    if not OPENAI_API_KEY:
        st.error("OpenAI API key is not set. Please add OPENAI_API_KEY to your .env file.")
        return None
        
    try:
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": """You are a medical assistant that extracts condition information from transcribed text. 
                Extract the following information in JSON format. Return ONLY a valid JSON object with these exact fields:
                {
                    "condition_name": "name of the condition",
                    "condition_text": "description of the condition" or null,
                    "recorded_date": "YYYY-MM-DD" or null,
                    "clinical_status": "active" or "inactive" or "resolved",
                    "category": "Problem" or "Diagnosis" or "Sympt" or "Other",
                    "onset_date": "YYYY-MM-DD" or null,
                    "is_relevant": true or false,
                    "relevance_feedback": "explanation of why the input is or isn't relevant"
                }
                
                If the input is not about a medical condition or is irrelevant:
                - Set is_relevant to false
                - Provide a clear explanation in relevance_feedback
                - Set all other fields to null
                
                If the input is about a medical condition:
                - Set is_relevant to true
                - Set relevance_feedback to "Input is relevant to medical conditions"
                - Fill in the other fields as appropriate
                
                If any information is not mentioned, use null for that field.
                Do not include any additional text or explanation, only the JSON object."""},
                {"role": "user", "content": transcription}
            ],
            temperature=0.3
        )
        
        # Extract the JSON from the response
        try:
            # Get the content and clean it
            content = response.choices[0].message.content.strip()
            
            # Remove any markdown code block markers if present
            content = content.replace('```json', '').replace('```', '').strip()
            
            # Parse the JSON
            extracted_data = json.loads(content)
            
            # Validate the structure
            required_fields = {
                "condition_name": (str, type(None)),
                "condition_text": (str, type(None)),
                "recorded_date": (str, type(None)),
                "clinical_status": (str, type(None)),
                "category": (str, type(None)),
                "onset_date": (str, type(None)),
                "is_relevant": bool,
                "relevance_feedback": str
            }
            
            # Check if all required fields are present and of correct type
            for field, expected_type in required_fields.items():
                if field not in extracted_data:
                    st.error(f"Missing required field: {field}")
                    return None
                    
                if not isinstance(extracted_data[field], expected_type):
                    st.error(f"Invalid type for field {field}. Expected {expected_type}, got {type(extracted_data[field])}")
                    return None
            
            # Check if the input is relevant
            if not extracted_data['is_relevant']:
                st.warning(f"⚠️ {extracted_data['relevance_feedback']}")
                st.info("Please try again with information about a medical condition.")
                return None
            
            return extracted_data
            
        except json.JSONDecodeError as e:
            st.error(f"Failed to parse GPT response as JSON: {str(e)}")
            st.error(f"Raw response: {content}")
            return None
            
    except Exception as e:
        st.error(f"Error processing with GPT: {str(e)}")
        return None

def show_manual_conditions_form():
    """
    Display form for manually entering conditions
    """
    st.subheader("Add New Condition")
    
    # Voice Input Section
    st.markdown("### 🎤 Voice Input (Optional)")
    st.info("You can use voice input to fill the form. Click the button below to start recording.")
    
    # Check if OpenAI API key is set
    if not OPENAI_API_KEY:
        st.warning("⚠️ OpenAI API key is not set. Voice transcription will work, but AI processing will be disabled.")
        st.info("To enable AI processing, add your OpenAI API key to the .env file as OPENAI_API_KEY=your_key_here")
    
    # Initialize session state for transcription if not exists
    if 'transcription' not in st.session_state:
        st.session_state.transcription = None
    if 'gpt_extracted_data' not in st.session_state:
        st.session_state.gpt_extracted_data = None
    if 'processed_audio' not in st.session_state:
        st.session_state.processed_audio = False
    
    # Record audio
    audio_data = mic_recorder(
        start_prompt="🎤 Start Recording",
        stop_prompt="⏹️ Stop Recording",
        use_container_width=True
    )
    
    # Process audio if recorded and not already processed
    if audio_data and audio_data['bytes'] and not st.session_state.processed_audio:
        st.audio(audio_data['bytes'], format="audio/webm")
        
        # Save to temp file and transcribe
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as f:
            f.write(audio_data['bytes'])
            temp_audio_path = f.name
        
        # Transcribe with Whisper
        with st.spinner("Transcribing..."):
            model = whisper.load_model("base")
            result = model.transcribe(temp_audio_path)
            st.session_state.transcription = result["text"]
            st.success("Transcription complete!")
            
            # Display transcription
            st.markdown("**Transcription:**")
            st.markdown(st.session_state.transcription)
            
            # Process with GPT only if API key is available
            if OPENAI_API_KEY:
                with st.spinner("Processing with AI..."):
                    extracted_data = process_transcription_with_gpt(st.session_state.transcription)
                
                if extracted_data:
                    st.success("AI Processing Complete!")
                    
                    # Update session state with extracted data
                    st.session_state.condition_name = extracted_data.get('condition_name', '')
                    st.session_state.condition_text = extracted_data.get('condition_text', '')
                    st.session_state.recorded_date = datetime.strptime(extracted_data['recorded_date'], "%Y-%m-%d").date() if extracted_data.get('recorded_date') else datetime.now().date()
                    st.session_state.clinical_status = extracted_data.get('clinical_status', 'active')
                    st.session_state.category = extracted_data.get('category', 'Problem')
                    st.session_state.onset_date = datetime.strptime(extracted_data['onset_date'], "%Y-%m-%d").date() if extracted_data.get('onset_date') else None
                    
                    # Mark as processed
                    st.session_state.processed_audio = True
                    
                    # Force a rerun to update the form
                    st.rerun()
            else:
                st.info("AI processing is disabled. Please add your OpenAI API key to enable this feature.")
            
        os.remove(temp_audio_path)
    
    # Reset processed flag if no audio data
    if not audio_data or not audio_data['bytes']:
        st.session_state.processed_audio = False
    
    # Get existing conditions if any
    existing_conditions = get_conditions_by_user_id(st.session_state.user_id)
    saved_conditions = existing_conditions.get('api_response', {}) if existing_conditions else {'entry': []}
    
    # Debug section to show raw JSON data
    with st.expander("Debug: View Raw Database JSON", expanded=False):
        st.json(saved_conditions)
    
    # Handle both dictionary and list formats for saved_conditions
    if isinstance(saved_conditions, dict) and 'entry' in saved_conditions:
        entries = saved_conditions['entry']
    elif isinstance(saved_conditions, list):
        entries = saved_conditions
    else:
        entries = []
    
    # Get Gorilla ID from profile if it exists, otherwise use a default value
    profile = get_profile_by_user_id(st.session_state.user_id)
    gorilla_id = profile.get('gorilla_id') if profile else f"MANUAL_{st.session_state.user_id}"
    
    # Form for adding new condition
    with st.form("new_condition_form"):
        condition_name = st.text_input(
            "Condition Name",
            value=st.session_state.get('condition_name', '')
        )
        
        condition_text = st.text_area(
            "Condition Description (optional)",
            value=st.session_state.get('condition_text', '')
        )
        
        recorded_date = st.date_input(
            "Date Recorded",
            value=st.session_state.get('recorded_date', datetime.now().date())
        )
        
        clinical_status = st.selectbox(
            "Clinical Status",
            ["active", "inactive", "resolved"],
            index=["active", "inactive", "resolved"].index(st.session_state.get('clinical_status', 'active'))
        )
        
        category = st.selectbox(
            "Category",
            ["Problem", "Diagnosis", "Sympt", "Other"],
            index=["Problem", "Diagnosis", "Sympt", "Other"].index(st.session_state.get('category', 'Problem'))
        )
        
        onset_date = st.date_input(
            "Onset Date (if known)",
            value=st.session_state.get('onset_date', None)
        )
        
        submitted = st.form_submit_button("Add Condition")
        if submitted:
            if condition_name:
                # Create a new condition entry in FHIR format
                new_condition = {
                    'resource': {
                        'resourceType': 'Condition',
                        'code': {
                            'text': condition_name,
                            'coding': [{
                                'display': condition_name
                            }]
                        },
                        'assertedDate': recorded_date.strftime("%Y-%m-%d"),
                        'clinicalStatus': {
                            'coding': [{
                                'system': 'http://terminology.hl7.org/CodeSystem/condition-clinical',
                                'code': clinical_status,
                                'display': clinical_status.capitalize()
                            }]
                        },
                        'category': [{
                            'coding': [{
                                'system': 'http://terminology.hl7.org/CodeSystem/condition-category',
                                'code': category.upper(),
                                'display': category
                            }]
                        }],
                        'text': {
                            'status': 'generated',
                            'div': f'<div xmlns="http://www.w3.org/1999/xhtml">{condition_text if condition_text else condition_name}</div>'
                        }
                    }
                }
                
                if onset_date:
                    new_condition['resource']['onsetPeriod'] = {
                        'start': onset_date.strftime("%Y-%m-%d")
                    }
                
                # Tokenize the condition text if available
                if condition_text:
                    tokenized_data = tokenize_medical_text(condition_text)
                    if tokenized_data:
                        new_condition['resource']['tokenized_data'] = tokenized_data
                
                # Check for duplicate
                if check_duplicate_condition(st.session_state.user_id, new_condition):
                    st.warning("This condition already exists in your records.")
                else:
                    # Add to existing conditions
                    if isinstance(saved_conditions, dict):
                        if 'entry' not in saved_conditions:
                            saved_conditions['entry'] = []
                        saved_conditions['entry'].append(new_condition)
                    else:
                        saved_conditions.append(new_condition)
                    
                    if save_conditions(st.session_state.user_id, gorilla_id, saved_conditions):
                        st.success(f"Added condition: {condition_name}")
                        # Clear session state after successful submission
                        for key in ['condition_name', 'condition_text', 'recorded_date', 'clinical_status', 'category', 'onset_date']:
                            if key in st.session_state:
                                del st.session_state[key]
                    else:
                        st.error("Failed to save condition. Please try again.")
            else:
                st.error("Please enter a condition name")

def show_saved_conditions():
    """
    Display conditions that have been saved to the database
    """
    st.subheader("Your Saved Conditions")
    
    # Get saved conditions from database
    existing_conditions = get_conditions_by_user_id(st.session_state.user_id)
    if not existing_conditions or not existing_conditions.get('api_response'):
        st.info("No conditions have been saved yet.")
        return
    
    saved_conditions = existing_conditions['api_response']
    
    if not saved_conditions:
        st.info("No conditions have been saved yet.")
        return
    
    # Ensure saved_conditions is a list of entries
    if isinstance(saved_conditions, dict) and 'entry' in saved_conditions:
        entries = saved_conditions['entry']
    elif isinstance(saved_conditions, list):
        entries = saved_conditions
    else:
        st.error("Invalid data format in saved conditions")
        return
    
    # Organize conditions by status
    active_conditions = []
    inactive_conditions = []
    unknown_conditions = []
    
    for entry in entries:
        # Ensure entry is a dictionary
        if not isinstance(entry, dict):
            continue
            
        # Get the resource, handling both direct resource and nested resource cases
        resource = entry.get('resource', {}) if isinstance(entry.get('resource'), dict) else entry
        
        if not resource:
            continue
        
        # Extract condition details with safe access
        code = resource.get('code', {})
        condition_name = code.get('text', '')
        if not condition_name and isinstance(code.get('coding'), list) and code.get('coding'):
            coding = code['coding'][0]
            condition_name = coding.get('display', 'Unknown Condition')
        
        recorded_date = resource.get('assertedDate', '')
        if recorded_date:
            recorded_date = recorded_date.split('T')[0]
        
        # Extract clinical status properly
        clinical_status = 'unknown'
        clinical_status_obj = resource.get('clinicalStatus', {})
        if isinstance(clinical_status_obj, dict):
            coding = clinical_status_obj.get('coding', [{}])[0]
            if isinstance(coding, dict):
                clinical_status = coding.get('code', 'unknown')
        elif isinstance(clinical_status_obj, str):
            clinical_status = clinical_status_obj.lower()
        
        # Get onset date if available
        onset_period = resource.get('onsetPeriod', {})
        onset_date = onset_period.get('start', '') if isinstance(onset_period, dict) else ''
        if onset_date:
            onset_date = onset_date.split('T')[0]
        
        # Get category if available
        category = ''
        category_obj = resource.get('category', [{}])[0] if isinstance(resource.get('category'), list) else {}
        if isinstance(category_obj, dict):
            category_coding = category_obj.get('coding', [{}])[0] if isinstance(category_obj.get('coding'), list) else {}
            category = category_coding.get('display', '')
        
        # Get condition text if available
        condition_text = ''
        text_obj = resource.get('text', {})
        if isinstance(text_obj, dict):
            condition_text = text_obj.get('div', '')
            if condition_text:
                # Remove HTML tags
                import re
                condition_text = re.sub('<[^<]+?>', '', condition_text)
        
        condition_data = {
            'name': condition_name,
            'text': condition_text,
            'recorded_date': recorded_date,
            'status': clinical_status,
            'category': category,
            'onset_date': onset_date
        }
        
        if clinical_status == 'active':
            active_conditions.append(condition_data)
        elif clinical_status == 'inactive':
            inactive_conditions.append(condition_data)
        else:
            unknown_conditions.append(condition_data)
    
    # Year filter
    all_years = sorted(set(
        condition['recorded_date'].split('-')[0] 
        for condition in active_conditions + inactive_conditions + unknown_conditions 
        if condition['recorded_date']
    ), reverse=True)
    
    selected_year = st.selectbox(
        "Filter by Year",
        ["All Years"] + all_years,
        key="saved_year_filter"
    )
    
    # Filter conditions by year if selected
    def filter_by_year(conditions_list):
        if selected_year == "All Years":
            return conditions_list
        return [
            condition for condition in conditions_list 
            if condition['recorded_date'] and condition['recorded_date'].startswith(selected_year)
        ]
    
    active_conditions = filter_by_year(active_conditions)
    inactive_conditions = filter_by_year(inactive_conditions)
    unknown_conditions = filter_by_year(unknown_conditions)
    
    # Display conditions in expanders by status
    if active_conditions:
        with st.expander(f"Active Conditions ({len(active_conditions)})", expanded=True):
            for condition in active_conditions:
                display_condition_card(condition)
    
    if inactive_conditions:
        with st.expander(f"Inactive Conditions ({len(inactive_conditions)})"):
            for condition in inactive_conditions:
                display_condition_card(condition)
    
    if unknown_conditions:
        with st.expander(f"Unknown Status Conditions ({len(unknown_conditions)})"):
            for condition in unknown_conditions:
                display_condition_card(condition)

def main():
    if not st.session_state.get("logged_in"):
        st.switch_page("pages/1_Login.py")
        return

    # Back button
    if st.button("← Back to Dashboard", key="back_to_dashboard"):
        st.switch_page("pages/2_Dashboard.py")

    st.title("Your Conditions")
    
    # Initialize session state for method selection if not exists
    if "conditions_method" not in st.session_state:
        st.session_state.conditions_method = "Saved Conditions"

    # Method selection
    method = st.radio(
        "Select how you would like to manage your conditions:",
        ["Saved Conditions", "Import from Central Health System", "Enter Manually"],
        horizontal=True,
        label_visibility="collapsed"
    )

    # Reset session state when switching methods
    if st.session_state.conditions_method != method:
        st.session_state.conditions_method = method

    # Show appropriate section based on selection
    if method == "Saved Conditions":
        show_saved_conditions()
    elif method == "Import from Central Health System":
        show_imported_conditions()
    else:
        show_manual_conditions_form()

if __name__ == "__main__":
    main() 