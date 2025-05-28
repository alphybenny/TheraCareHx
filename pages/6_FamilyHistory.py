import streamlit as st
import requests
import os
from dotenv import load_dotenv
from database import get_profile_by_user_id, save_family_history, get_family_history_by_user_id, check_and_init_db, check_duplicate_family_history
import json
from streamlit_mic_recorder import mic_recorder
import whisper
import tempfile
import openai

# Load environment variables
load_dotenv()
API_BASE_URL = os.getenv('API_BASE_URL')
IMO_SEARCH_URL = f"{API_BASE_URL}/imo-core-search"
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Ensure FFmpeg is available to Whisper
os.environ["PATH"] += os.pathsep + r"C:\Program Files\ffmpeg-master-latest-win64-gpl-shared\ffmpeg-master-latest-win64-gpl-shared\bin"

st.set_page_config(
    page_title="TheraCare - Family History",
    page_icon="👨‍👩‍👧‍👦",
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
        
        .history-card {
            background-color: #1a1a1a;
            border: 1px solid #333;
            border-radius: 10px;
            padding: 1.5rem;
            margin-bottom: 1rem;
        }
        
        .history-title {
            font-size: 1.2rem;
            font-weight: 600;
            color: #fff;
            margin-bottom: 0.5rem;
        }
        
        .history-date {
            color: #888;
            font-size: 0.9rem;
            margin-bottom: 0.5rem;
        }
        
        .history-relationship {
            color: #ccc;
            margin-bottom: 0.5rem;
        }
        
        .history-status {
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

def get_family_history(gorilla_id):
    """
    Fetch family history for a patient from the API
    """
    try:
        history_url = f"{API_BASE_URL}/family-history/{gorilla_id}"
        response = requests.get(history_url)
        
        if response.status_code == 200:
            data = response.json()
            
            # Check if we have a valid FHIR Bundle
            if isinstance(data, dict) and data.get('resourceType') == 'Bundle' and 'entry' in data:
                return data
            else:
                st.warning("Unexpected API response format")
                return None
        else:
            st.error(f"Error fetching family history: HTTP {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error fetching family history: {str(e)}")
        return None

def show_saved_history():
    """
    Display family history that has been saved to the database
    """
    st.subheader("Your Saved Family History")
    
    # Get saved history from database
    existing_history = get_family_history_by_user_id(st.session_state.user_id)
    if not existing_history or not existing_history.get('api_response'):
        st.info("No family history has been saved yet.")
        return
    
    saved_history = existing_history['api_response']
    
    if not saved_history or not isinstance(saved_history, dict) or 'entry' not in saved_history:
        st.info("No family history has been saved yet.")
        return
    
    # Display history entries
    for entry in saved_history['entry']:
        resource = entry.get('resource', {})
        if not resource:
            continue
            
        with st.container():
            col1, col2 = st.columns([3, 1])
            
            with col1:
                # Relationship
                relationship = resource.get('relationship', {})
                relationship_text = relationship.get('text', '')
                if not relationship_text and 'coding' in relationship:
                    relationship_text = relationship['coding'][0].get('display', 'Unknown')
                
                # Gender
                gender = resource.get('gender', '')
                if gender:
                    relationship_text = f"{relationship_text} ({gender})"
                
                st.markdown(f"**{relationship_text}**")
                
                # Born Date
                born_date = resource.get('bornDate', '')
                if born_date:
                    st.caption(f"Born: {born_date}")
                
                # Conditions
                conditions = resource.get('condition', [])
                if not conditions:
                    st.text("No known conditions")
                else:
                    for condition in conditions:
                        code = condition.get('code', {})
                        condition_text = code.get('text', '')
                        if not condition_text and 'coding' in code:
                            condition_text = code['coding'][0].get('display', 'Unknown Condition')
                        
                        # Onset Age
                        onset_age = condition.get('onsetAge', {})
                        age_text = ''
                        if onset_age:
                            age_value = onset_age.get('value', '')
                            age_unit = onset_age.get('unit', '')
                            if age_value:
                                age_text = f" (Age {age_value}{age_unit})"
                        
                        # Cause of Death
                        is_cause_of_death = False
                        extensions = condition.get('extension', []) or []
                        for ext in extensions:
                            if ext and isinstance(ext, dict) and ext.get('url') == 'https://www.healthgorilla.com/fhir/StructureDefinition/familymemberhistory-cause-of-death':
                                is_cause_of_death = ext.get('valueBoolean', False)
                                break
                        
                        if is_cause_of_death:
                            condition_text = f"💀 {condition_text} (Cause of Death)"
                        
                        st.text(f"• {condition_text}{age_text}")
            
            with col2:
                status = resource.get('status', 'health-unknown')
                status_color = "#2d89ef" if status == 'health-unknown' else "#333"
                status_text = status.replace('-', ' ').title()
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

def show_imported_history():
    """
    Display family history imported from the central health system
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
        
        # Get family history from API
        history = get_family_history(st.session_state.gorilla_id)
        
        if history and isinstance(history, dict) and 'entry' in history:
            # Display history entries
            for entry in history['entry']:
                resource = entry.get('resource', {})
                if not resource:
                    continue
                    
                with st.container():
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        # Relationship
                        relationship = resource.get('relationship', {})
                        relationship_text = relationship.get('text', '')
                        if not relationship_text and 'coding' in relationship:
                            relationship_text = relationship['coding'][0].get('display', 'Unknown')
                        
                        # Gender
                        gender = resource.get('gender', '')
                        if gender:
                            relationship_text = f"{relationship_text} ({gender})"
                        
                        st.markdown(f"**{relationship_text}**")
                        
                        # Born Date
                        born_date = resource.get('bornDate', '')
                        if born_date:
                            st.caption(f"Born: {born_date}")
                        
                        # Conditions
                        conditions = resource.get('condition', [])
                        if not conditions:
                            st.text("No known conditions")
                        else:
                            for condition in conditions:
                                code = condition.get('code', {})
                                condition_text = code.get('text', '')
                                if not condition_text and 'coding' in code:
                                    condition_text = code['coding'][0].get('display', 'Unknown Condition')
                                
                                # Onset Age
                                onset_age = condition.get('onsetAge', {})
                                age_text = ''
                                if onset_age:
                                    age_value = onset_age.get('value', '')
                                    age_unit = onset_age.get('unit', '')
                                    if age_value:
                                        age_text = f" (Age {age_value}{age_unit})"
                                
                                # Cause of Death
                                is_cause_of_death = False
                                for ext in condition.get('extension', []):
                                    if ext.get('url') == 'https://www.healthgorilla.com/fhir/StructureDefinition/familymemberhistory-cause-of-death':
                                        is_cause_of_death = ext.get('valueBoolean', False)
                                
                                if is_cause_of_death:
                                    condition_text = f"💀 {condition_text} (Cause of Death)"
                                
                                st.text(f"• {condition_text}{age_text}")
                    
                    with col2:
                        status = resource.get('status', 'health-unknown')
                        status_color = "#2d89ef" if status == 'health-unknown' else "#333"
                        status_text = status.replace('-', ' ').title()
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
            
            # Add save button with duplicate checking
            if st.button("Save Family History to Database", type="primary"):
                with st.spinner("Saving family history..."):
                    # Check for duplicates
                    duplicates = []
                    non_duplicates = []
                    for entry in history['entry']:
                        if check_duplicate_family_history(st.session_state.user_id, entry):
                            duplicates.append(entry)
                        else:
                            non_duplicates.append(entry)
                    
                    if duplicates:
                        st.warning(f"Found {len(duplicates)} duplicate family history entries. They will not be added again.")
                    
                    if non_duplicates:
                        # Create a new bundle with only non-duplicate entries
                        new_history = {
                            'resourceType': 'Bundle',
                            'type': 'searchset',
                            'entry': non_duplicates
                        }
                        
                        if save_family_history(st.session_state.user_id, st.session_state.gorilla_id, new_history):
                            st.success("Successfully saved new family history entries to your profile!")
                        else:
                            st.error("Failed to save family history. Please try again.")
                    else:
                        st.info("No new family history entries to save.")
        else:
            st.info("No family history found in your health record.")
    else:
        st.info("Your profile was created manually. To view your family history, please import your profile from the central health system.")
        if st.button("Import Profile"):
            st.switch_page("pages/4_EditProfile.py")

def search_imo_conditions(text):
    """
    Search for conditions using IMO Core Search API
    """
    try:
        response = requests.get(f"{IMO_SEARCH_URL}?text={text}")
        if response.status_code == 200:
            data = response.json()
            # Extract items from the SearchTermResponse
            if 'SearchTermResponse' in data and 'items' in data['SearchTermResponse']:
                return data['SearchTermResponse']['items']
        return None
    except Exception as e:
        st.error(f"Error searching conditions: {str(e)}")
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
                {"role": "system", "content": """You are a medical assistant that extracts family history information from transcribed text. 
                Extract the following information in JSON format. Return ONLY a valid JSON object with these exact fields:
                {
                    "relationship": "Father" or "Mother" or "Sibling" or "Grandparent" or "Other",
                    "gender": "male" or "female" or "other" or "unknown",
                    "birth_year": "year" or null,
                    "conditions": [
                        {
                            "name": "condition name",
                            "age_at_onset": number or null,
                            "is_cause_of_death": true or false
                        }
                    ],
                    "notes": "any additional information" or null,
                    "is_relevant": true or false,
                    "relevance_feedback": "explanation of why the input is or isn't relevant"
                }
                
                If the input is not about family medical history or is irrelevant:
                - Set is_relevant to false
                - Provide a clear explanation in relevance_feedback
                - Set all other fields to null
                - Set conditions to empty array
                
                If the input is about family medical history:
                - Set is_relevant to true
                - Set relevance_feedback to "Input is relevant to family medical history"
                - Fill in the other fields as appropriate
                - Include all mentioned conditions in the conditions array
                
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
                "relationship": (str, type(None)),
                "gender": (str, type(None)),
                "birth_year": (str, int, type(None)),  # Updated to accept int
                "conditions": list,
                "notes": (str, type(None)),
                "is_relevant": bool,
                "relevance_feedback": str
            }
            
            # Check if all required fields are present
            for field in required_fields:
                if field not in extracted_data:
                    st.error(f"Missing required field: {field}")
                    return None
            
            # Check if the input is relevant first
            if not extracted_data.get('is_relevant', False):
                st.warning(f"⚠️ {extracted_data.get('relevance_feedback', 'Input is not relevant to family medical history.')}")
                st.info("Please try again with information about family medical history.")
                return None
            
            # Validate field types
            for field, expected_type in required_fields.items():
                value = extracted_data[field]
                
                # Special handling for boolean fields
                if field == 'is_relevant':
                    if not isinstance(value, bool):
                        extracted_data[field] = False
                    continue
                
                # Special handling for birth_year
                if field == 'birth_year':
                    if value is not None:
                        if isinstance(value, int):
                            extracted_data[field] = str(value)
                        elif not isinstance(value, str):
                            st.error(f"Invalid type for field {field}. Expected string or integer, got {type(value)}")
                            return None
                    continue
                
                # For other fields, check if the type is valid
                if value is not None and not isinstance(value, expected_type):
                    st.error(f"Invalid type for field {field}. Expected {expected_type}, got {type(value)}")
                    return None
            
            # Validate conditions array
            if not isinstance(extracted_data.get('conditions'), list):
                st.error("Conditions must be an array")
                return None
            
            for condition in extracted_data['conditions']:
                if not isinstance(condition, dict):
                    st.error("Each condition must be an object")
                    return None
                
                required_condition_fields = {
                    "name": str,
                    "age_at_onset": (int, type(None)),
                    "is_cause_of_death": bool
                }
                
                for field, expected_type in required_condition_fields.items():
                    if field not in condition:
                        st.error(f"Missing required field in condition: {field}")
                        return None
                    
                    value = condition[field]
                    if value is not None and not isinstance(value, expected_type):
                        st.error(f"Invalid type for condition field {field}. Expected {expected_type}, got {type(value)}")
                        return None
            
            return extracted_data
            
        except json.JSONDecodeError as e:
            st.error(f"Failed to parse GPT response as JSON: {str(e)}")
            st.error(f"Raw response: {content}")
            return None
            
    except Exception as e:
        st.error(f"Error processing with GPT: {str(e)}")
        return None

def clear_all_form_state():
    """
    Clear all form-related session state
    """
    print("Clearing all form state...")
    # Clear search and condition state
    st.session_state.search_results = []
    st.session_state.selected_conditions = []
    st.session_state.search_texts = []
    st.session_state.search_text = ""
    st.session_state.trigger_search = False
    
    # Clear voice input state
    st.session_state.transcription = None
    st.session_state.gpt_extracted_data = None
    st.session_state.processed_audio = False
    st.session_state.audio_data = None
    st.session_state.is_processing = False
    
    # Clear form field state
    st.session_state.relationship = "Father"
    st.session_state.gender = "male"
    st.session_state.birth_year = ""
    st.session_state.condition = ""
    st.session_state.age = None
    st.session_state.is_cause_of_death = False
    st.session_state.notes = ""
    
    # Clear page state
    st.session_state.page_loaded = False
    print("All form state cleared")

def show_manual_history_form():
    """
    Display form for manually entering family history with two paths:
    1. Manual form filling with search
    2. Audio input with transcription and GPT processing
    """
    print("\n=== Starting show_manual_history_form ===")
    
    # Initialize session state variables
    if 'form_mode' not in st.session_state:
        st.session_state.form_mode = 'manual'  # 'manual' or 'audio'
    if 'form_data' not in st.session_state:
        st.session_state.form_data = {
            'relationship': 'Father',
            'gender': 'male',
            'birth_year': '',
            'conditions': [],
            'age_at_onset': None,
            'is_cause_of_death': False,
            'notes': ''
        }
    if 'search_results' not in st.session_state:
        st.session_state.search_results = []
    if 'selected_conditions' not in st.session_state:
        st.session_state.selected_conditions = []
    if 'is_processing' not in st.session_state:
        st.session_state.is_processing = False
    if 'transcription' not in st.session_state:
        st.session_state.transcription = None
    
    # Mode selection
    st.subheader("Add New Family History Entry")
    mode = st.radio(
        "Choose input method:",
        ["Manual Entry", "Voice Input"],
        horizontal=True,
        key="input_mode"
    )
    
    if mode == "Voice Input":
        st.session_state.form_mode = 'audio'
        handle_audio_input()
    else:
        st.session_state.form_mode = 'manual'
        handle_manual_input()
    
    print("=== Ending show_manual_history_form ===\n")

def handle_audio_input():
    """Handle the audio input path"""
    st.markdown("### 🎤 Voice Input")
    st.info("Record your family history information. The system will transcribe and process it automatically.")
    
    # Record audio
    audio_data = mic_recorder(
        start_prompt="🎤 Start Recording",
        stop_prompt="⏹️ Stop Recording",
        use_container_width=True
    )
    
    # Process audio if we have new data and not already processing
    if (audio_data and 
        audio_data['bytes'] and 
        not st.session_state.is_processing):
        
        print("Starting audio processing...")
        st.session_state.is_processing = True
        
        st.audio(audio_data['bytes'], format="audio/webm")
        
        # Save to temp file and transcribe
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as f:
            f.write(audio_data['bytes'])
            temp_audio_path = f.name
        
        try:
            # Transcribe with Whisper
            with st.spinner("Transcribing..."):
                print("Starting transcription...")
                model = whisper.load_model("base")
                result = model.transcribe(temp_audio_path)
                st.session_state.transcription = result["text"]
                print("Transcription complete:", st.session_state.transcription[:50] + "...")
                st.success("Transcription complete!")
                
                # Display transcription
                st.markdown("**Transcription:**")
                st.markdown(st.session_state.transcription)
                
                # Process with GPT
                if OPENAI_API_KEY:
                    with st.spinner("Processing with AI..."):
                        print("Starting GPT processing...")
                        extracted_data = process_transcription_with_gpt(st.session_state.transcription)
                    
                    if extracted_data and extracted_data.get('is_relevant', False):
                        print("GPT processing complete, updating form data...")
                        st.success("AI Processing Complete!")
                        
                        # Update form data
                        st.session_state.form_data.update({
                            'relationship': extracted_data.get('relationship', 'Father'),
                            'gender': extracted_data.get('gender', 'male'),
                            'birth_year': extracted_data.get('birth_year', ''),
                            'notes': extracted_data.get('notes', '')
                        })
                        
                        # Process conditions
                        conditions = extracted_data.get('conditions', [])
                        if conditions:
                            st.session_state.search_results = []
                            for condition in conditions:
                                results = search_imo_conditions(condition['name'])
                                if results:
                                    st.session_state.search_results.extend(results)
                        
                        # Show the pre-filled form
                        show_family_history_form()
                    else:
                        st.warning("Could not extract relevant family history information. Please try again or use manual entry.")
                else:
                    st.info("AI processing is disabled. Please add your OpenAI API key to enable this feature.")
        except Exception as e:
            print(f"Error in audio processing: {str(e)}")
            st.error(f"Error processing audio: {str(e)}")
            st.warning("Please try recording again.")
        finally:
            os.remove(temp_audio_path)
            st.session_state.is_processing = False
    else:
        # Show the form even if no audio is being processed
        show_family_history_form()

def handle_manual_input():
    """Handle the manual input path"""
    st.markdown("### ✍️ Manual Entry")
    st.info("Fill in the form below to add family history information.")
    
    # Initialize search state if not exists
    if 'search_results' not in st.session_state:
        st.session_state.search_results = []
    if 'selected_conditions' not in st.session_state:
        st.session_state.selected_conditions = []
    if 'last_search' not in st.session_state:
        st.session_state.last_search = ""
    
    # Search for conditions
    col1, col2 = st.columns([3, 1])
    with col1:
        search_input = st.text_input("Search for medical conditions", key="new_condition_search")
    with col2:
        st.markdown("###")  # For vertical alignment
        if st.button("Search", key="new_search_button"):
            if search_input:
                st.session_state.last_search = search_input
                with st.spinner("Searching conditions..."):
                    results = search_imo_conditions(search_input)
                    if results:
                        # Add search text and unique identifier to each result
                        for idx, result in enumerate(results):
                            result['search_text'] = search_input
                            # Create a unique identifier using available fields
                            unique_parts = [
                                search_input,
                                str(idx),
                                result.get('kndg_id', ''),
                                result.get('ICD10CM_CODE', ''),
                                result.get('kndg_title', '')
                            ]
                            # Join non-empty parts with underscores
                            result['unique_id'] = '_'.join(part for part in unique_parts if part)
                        st.session_state.search_results.extend(results)
                        st.success(f"Found {len(results)} results for '{search_input}'")
                    else:
                        st.warning(f"No matching conditions found for '{search_input}'")
            else:
                st.warning("Please enter a search term")
    
    # Display search history and results
    if st.session_state.search_results:
        st.markdown("### 🔍 Search Results")
        
        # Group results by search term
        search_groups = {}
        for result in st.session_state.search_results:
            search_text = result.get('search_text', 'Unknown Search')
            if search_text not in search_groups:
                search_groups[search_text] = []
            search_groups[search_text].append(result)
        
        # Display results by search group
        for search_text, results in search_groups.items():
            with st.expander(f"Results for: {search_text}"):
                for result in results:
                    condition_text = f"{result.get('kndg_title', '')} (ICD-10: {result.get('ICD10CM_TITLE', 'N/A')})"
                    # Use the unique identifier we created earlier
                    unique_key = f"condition_{result.get('unique_id', '')}"
                    if st.checkbox(condition_text, key=unique_key):
                        if result not in st.session_state.selected_conditions:
                            st.session_state.selected_conditions.append(result)
    
    # Display selected conditions with remove option
    if st.session_state.selected_conditions:
        st.markdown("### Selected Conditions")
        for idx, condition in enumerate(st.session_state.selected_conditions):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"- {condition.get('kndg_title', '')}")
            with col2:
                if st.button("Remove", key=f"remove_{condition.get('unique_id', idx)}"):
                    st.session_state.selected_conditions.pop(idx)
                    st.rerun()
    
    # Show the form
    show_family_history_form()

def show_family_history_form():
    """Display the family history form with current data"""
    # Relationship
    relationship = st.selectbox(
        "Relationship",
        ["Father", "Mother", "Sibling", "Grandparent", "Other"],
        index=["Father", "Mother", "Sibling", "Grandparent", "Other"].index(
            st.session_state.form_data.get('relationship', "Father")
        )
    )
    
    # Gender
    gender = st.selectbox(
        "Gender",
        ["male", "female", "other", "unknown"],
        index=["male", "female", "other", "unknown"].index(
            st.session_state.form_data.get('gender', "male")
        )
    )
    
    # Birth Year
    birth_year = st.text_input(
        "Birth Year (optional)",
        value=st.session_state.form_data.get('birth_year', '')
    )
    
    # Condition Selection
    if st.session_state.search_results:
        st.markdown("### 🔍 Select Conditions")
        st.info("Select the conditions that match your family member's medical history.")
        
        # Create a unique index for each condition
        for idx, result in enumerate(st.session_state.search_results):
            condition_text = f"{result.get('kndg_title', '')} (ICD-10: {result.get('ICD10CM_TITLE', 'N/A')})"
            # Create a unique key using both the index and the condition title
            unique_key = f"condition_{idx}_{result.get('kndg_title', '').replace(' ', '_')}"
            if st.checkbox(condition_text, key=unique_key):
                if result not in st.session_state.selected_conditions:
                    st.session_state.selected_conditions.append(result)
    
    # Display selected conditions
    if st.session_state.selected_conditions:
        st.markdown("### Selected Conditions")
        for condition in st.session_state.selected_conditions:
            st.markdown(f"- {condition.get('kndg_title', '')}")
    
    # Age at Onset
    age_at_onset = st.number_input(
        "Age at Onset (if known)",
        min_value=0,
        max_value=120,
        value=st.session_state.form_data.get('age_at_onset')
    )
    
    # Cause of Death
    is_cause_of_death = st.checkbox(
        "Cause of Death",
        value=st.session_state.form_data.get('is_cause_of_death', False)
    )
    
    # Notes
    notes = st.text_area(
        "Additional Notes",
        value=st.session_state.form_data.get('notes', '')
    )
    
    # Submit button
    if st.button("Add Family History Entry"):
        if relationship and st.session_state.selected_conditions:
            try:
                # Create extensions array
                extensions = []
                
                # Add cause of death extension if applicable
                if is_cause_of_death:
                    extensions.append({
                        'url': 'https://www.healthgorilla.com/fhir/StructureDefinition/familymemberhistory-cause-of-death',
                        'valueBoolean': True
                    })
                
                # Add IMO search data extension for each selected condition
                for condition in st.session_state.selected_conditions:
                    imo_data = {
                        'kndg_title': condition.get('kndg_title'),
                        'ICD10CM_TITLE': condition.get('ICD10CM_TITLE'),
                        'SNOMEDCT_TITLE': condition.get('SNOMEDCT_TITLE'),
                        'kndg_id': condition.get('kndg_id'),
                        'ICD10CM_CODE': condition.get('ICD10CM_CODE'),
                        'SNOMEDCT_CODE': condition.get('SNOMEDCT_CODE')
                    }
                    extensions.append({
                        'url': 'https://www.healthgorilla.com/fhir/StructureDefinition/imo-core-search-data',
                        'valueString': json.dumps(imo_data)
                    })
                
                # Create new history entry
                new_entry = create_family_history_entry(
                    relationship=relationship,
                    gender=gender,
                    birth_year=birth_year,
                    conditions=st.session_state.selected_conditions,
                    age_at_onset=age_at_onset,
                    extensions=extensions,
                    notes=notes
                )
                
                # Save to database
                if save_family_history_entry(new_entry):
                    st.success(f"Added family history entry: {relationship}")
                    clear_form_state()
                else:
                    st.error("Failed to save family history entry. Please try again.")
            except Exception as e:
                print(f"Error saving family history: {str(e)}")
                st.error(f"Error saving family history: {str(e)}")
        else:
            st.error("Please enter a relationship and select at least one condition")

def create_family_history_entry(relationship, gender, birth_year, conditions, age_at_onset, extensions, notes):
    """Create a new family history entry in FHIR format"""
    return {
        'resource': {
            'resourceType': 'FamilyMemberHistory',
            'relationship': {
                'text': relationship,
                'coding': [{
                    'code': {
                        'Father': 'FTH',
                        'Mother': 'MTH',
                        'Sibling': 'SIB',
                        'Grandparent': 'GRPRN',
                        'Other': 'OTH'
                    }.get(relationship, 'OTH'),
                    'display': relationship,
                    'system': 'urn:oid:2.16.840.1.113883.5.111'
                }]
            },
            'gender': gender,
            'condition': [{
                'code': {
                    'text': condition.get('kndg_title'),
                    'coding': [{
                        'display': condition.get('kndg_title')
                    }]
                },
                'onsetAge': {
                    'value': age_at_onset,
                    'unit': 'a'
                } if age_at_onset else None,
                'extension': extensions if extensions else None
            } for condition in conditions],
            'note': [{
                'text': notes
            }] if notes else None,
            'status': 'health-unknown'
        }
    }

def save_family_history_entry(new_entry):
    """Save a new family history entry to the database"""
    try:
        # Get existing history
        saved_history = get_family_history_by_user_id(st.session_state.user_id)
        if not saved_history:
            # Create new history if none exists
            saved_history = {
                'api_response': {
                    'resourceType': 'Bundle',
                    'type': 'searchset',
                    'entry': []
                }
            }
        
        # Add new entry to history
        saved_history['api_response']['entry'].append(new_entry)
        
        # Save to database
        return save_family_history(st.session_state.user_id, st.session_state.gorilla_id, saved_history['api_response'])
    except Exception as e:
        print(f"Error saving family history entry: {str(e)}")
        return False

def clear_form_state():
    """Clear the form state"""
    st.session_state.form_data = {
        'relationship': 'Father',
        'gender': 'male',
        'birth_year': '',
        'conditions': [],
        'age_at_onset': None,
        'is_cause_of_death': False,
        'notes': ''
    }
    st.session_state.search_results = []
    st.session_state.selected_conditions = []
    st.session_state.transcription = None
    st.session_state.is_processing = False
    st.session_state.condition_search = ""  # Clear search input

def main():
    if not st.session_state.get("logged_in"):
        st.switch_page("pages/1_Login.py")
        return

    # Clear all search-related session state if this is a fresh page load
    if "page_loaded" not in st.session_state or not st.session_state.page_loaded:
        st.session_state.page_loaded = True
        clear_form_state()

    # Back button
    if st.button("← Back to Dashboard", key="back_to_dashboard"):
        st.switch_page("pages/2_Dashboard.py")

    st.title("Family History")
    
    # Initialize session state for method selection if not exists
    if "history_method" not in st.session_state:
        st.session_state.history_method = "Saved History"
    
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

    # Method selection
    method = st.radio(
        "Select how you would like to manage your family history:",
        ["Saved History", "Import from Central Health System", "Enter Manually"],
        horizontal=True,
        label_visibility="collapsed"
    )

    # Reset session state when switching methods
    if st.session_state.history_method != method:
        st.session_state.history_method = method
        clear_form_state()
        st.session_state.page_loaded = False
        st.rerun()

    # Show appropriate section based on selection
    if method == "Saved History":
        show_saved_history()
    elif method == "Import from Central Health System":
        if not st.session_state.gorilla_id:
            st.warning("Please import your profile from the central health system first to access your family history.")
            if st.button("Import Profile"):
                st.switch_page("pages/4_EditProfile.py")
        else:
            show_imported_history()
    else:
        show_manual_history_form()

if __name__ == "__main__":
    main() 