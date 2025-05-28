# TheraCare Hx - Health History Management System

## Project Overview
TheraCare Hx is an innovative health management system that revolutionizes how patients and healthcare providers manage medical histories. By integrating with Health Gorilla's API, it provides a secure, user-friendly platform for comprehensive health information management.

## Key Features

### 1. User Authentication & Security
- Secure login and registration system
- JWT-based authentication
- Password-protected PDF reports
- Encrypted database storage
- Secure API communications

### 2. Health Information Management
- Personal profile management
- Health conditions tracking
- Family medical history recording
- Secure PDF report generation
- Voice-based input for medical conditions
- AI-powered medical text processing

### 3. Data Integration
- Health Gorilla API integration
- FHIR-compliant data structure
- Real-time data synchronization
- Secure data transmission

### 4. User Experience
- Intuitive dashboard interface
- Voice input capabilities
- Automated report generation
- Easy navigation and data entry
- Responsive design

## Technical Architecture

### Frontend
- Streamlit-based user interface
- Real-time data validation
- PDF report generation
- Voice recording integration

### Backend
- Python-based application logic
- PostgreSQL database
- JWT authentication
- API integration services

### APIs & Services
- Health Gorilla API
- OpenAI Whisper for voice processing
- GPT for medical text analysis
- LOF-CS595 Flask backend

## Prerequisites

Before running the application, ensure you have the following installed:
- Python 3.8 or higher
- PostgreSQL database
- pip (Python package manager)

## Project Structure

The project consists of two main components:
1. **LOF-CS595**: Flask backend service that handles API integrations
2. **TheraCare**: Streamlit frontend application

## Setup Instructions

### 1. Database Setup

1. Create a PostgreSQL database named `TheraCareDB`
2. Update the `.env` file with your database credentials:
   ```
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=TheraCareDB
   DB_USER=your_username
   DB_PASSWORD=your_password
   SECRET_KEY=your_secret_key_for_jwt
   ```

### 2. LOF Backend Setup

1. Navigate to the LOF-CS595 directory:
   ```bash
   cd LOF-CS595
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv myenv
   source myenv/bin/activate  # On Windows: myenv\Scripts\activate
   ```

3. Install required packages:
   ```bash
   pip install -r lof/requirements.txt
   ```

4. Update the LOF `.env` file with your credentials:
   ```
   client_id=your_client_id
   client_secret=your_client_secret
   ```

5. Start the LOF backend service:
   ```bash
   python lof/services.py
   ```

### 3. TheraCare Frontend Setup

1. Navigate to the TheraCare directory:
   ```bash
   cd ..
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

4. Start the Streamlit application:
   ```bash
   streamlit run app.py
   ```

## Usage Guide

1. **Registration**
   - Click on "Sign Up" to create a new account
   - Fill in your personal information
   - Set up a secure password

2. **Login**
   - Enter your username and password
   - Access your personalized dashboard

3. **Profile Management**
   - Update personal information
   - Add or modify health conditions
   - Record family medical history

4. **Health Report Generation**
   - Click "Download Health Report" on the dashboard
   - The system will generate a password-protected PDF
   - Save the displayed password securely
   - Use the password to open the PDF report

## Troubleshooting

1. **Database Connection Issues**
   - Verify PostgreSQL is running
   - Check database credentials in `.env`
   - Ensure database exists and is accessible

2. **API Integration Issues**
   - Verify LOF backend is running
   - Check API credentials in LOF `.env`
   - Ensure network connectivity

3. **PDF Generation Issues**
   - Verify PyPDF2 is installed
   - Check file permissions
   - Ensure sufficient disk space

