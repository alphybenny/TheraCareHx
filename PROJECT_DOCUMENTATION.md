# TheraCare Hx - Comprehensive Project Documentation

## Table of Contents
1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [APIs Integration](#apis-integration)
4. [Features](#features)
5. [Pages and Functionality](#pages-and-functionality)
6. [Security Implementation](#security-implementation)
7. [Database Schema](#database-schema)
8. [Technical Specifications](#technical-specifications)

## Project Overview

TheraCare Hx is a comprehensive health history management system that provides users with a secure platform to manage their medical information. The system integrates with Health Gorilla's API to fetch and manage health data while maintaining strict security and privacy standards.

## System Architecture

The application follows a three-tier architecture:

1. **Frontend Layer (Streamlit)**
   - User Interface
   - Client-side validation
   - Session management

2. **Backend Layer (LOF-CS595)**
   - API integrations
   - Data processing
   - Authentication services

3. **Database Layer (PostgreSQL)**
   - Data persistence
   - User information
   - Health records

## APIs Integration

### 1. Health Gorilla API
- **Purpose**: Fetch and manage health records
- **Endpoints Used**:
  - Patient data retrieval
  - Condition history
  - Family medical history
  - Authentication and authorization

### 2. Leap of Faith (LOF) API
- **Purpose**: Handle API authentication and token management
- **Services**:
  - Token generation
  - API request handling
  - Error management

### 3. IMO NLP Service
- **Purpose**: Process and analyze medical text
- **Features**:
  - Text tokenization
  - Medical terminology processing
  - Core search functionality

## Features

### 1. User Management
- Secure registration and login
- Profile management
- Session handling
- Password protection

### 2. Health Information Management
- Personal health records
- Medical conditions tracking
- Family medical history
- Health report generation

### 3. Data Security
- Encrypted data storage
- Secure API communications
- Password-protected PDF reports
- JWT-based authentication

### 4. Reporting
- Comprehensive health reports
- PDF generation with password protection
- Customizable report formats
- Data visualization

## Pages and Functionality

### 1. Login Page (`1_Login.py`)
- User authentication
- Session initialization
- Navigation to signup

### 2. Dashboard (`2_Dashboard.py`)
- User profile overview
- Health summary
- Quick access to features
- Report generation
- Navigation to other sections

### 3. Signup Page (`3_Signup.py`)
- New user registration
- Profile creation
- Initial data collection

### 4. Profile Management (`4_EditProfile.py`)
- Personal information update
- Contact details management
- Profile picture upload
- Medical information update

### 5. Conditions Management (`5_YourConditions.py`)
- Medical conditions tracking
- Condition history
- Treatment information
- Progress monitoring

### 6. Family History (`6_FamilyHistory.py`)
- Family medical records
- Genetic information
- Health history tracking
- Relationship mapping

## Security Implementation

### 1. Authentication
- JWT-based authentication
- Password hashing with bcrypt
- Session management
- Token validation

### 2. Data Protection
- Encrypted database storage
- Secure API communications
- Environment variable configuration
- Input validation

### 3. PDF Security
- Password protection
- Encryption
- Secure storage
- Access control

## Database Schema

### Tables
1. **users**
   - id (Primary Key)
   - username
   - email
   - password_hash
   - created_at

2. **profiles**
   - id (Primary Key)
   - user_id (Foreign Key)
   - gorilla_id
   - profile_data (JSONB)
   - created_at
   - updated_at

3. **conditions**
   - id (Primary Key)
   - user_id (Foreign Key)
   - gorilla_id
   - api_response (JSONB)
   - created_at
   - updated_at

4. **family_history**
   - id (Primary Key)
   - user_id (Foreign Key)
   - gorilla_id
   - api_response (JSONB)
   - created_at
   - updated_at

## Technical Specifications

### Frontend Technologies
- Streamlit 1.32.0
- ReportLab 4.0.4
- PyPDF2 3.0.1

### Backend Technologies
- Python 3.8+
- FastAPI 0.109.2
- Uvicorn 0.27.1

### Database
- PostgreSQL
- psycopg2-binary 2.9.9

### Security
- python-jose 3.3.0
- bcrypt 4.1.2
- passlib 1.7.4

### API Integration
- requests 2.31.0
- python-multipart 0.0.9
- pydantic 2.6.1

## Development Guidelines

### Code Structure
- Modular design
- Separation of concerns
- Clear documentation
- Error handling

### Security Best Practices
- Input validation
- Secure password storage
- API key management
- Error logging

### Testing
- Unit tests
- Integration tests
- Security testing
- Performance testing

## Deployment

### Requirements
- Python 3.8+
- PostgreSQL database
- Environment variables
- API credentials

### Steps
1. Database setup
2. Environment configuration
3. Dependencies installation
4. Application deployment
5. Security verification

## Support and Maintenance

### Documentation
- API documentation
- User guides
- Technical documentation
- Troubleshooting guides

### Monitoring
- Error logging
- Performance monitoring
- Security auditing
- User activity tracking

## Future Enhancements

### Planned Features
- Mobile application
- Advanced analytics
- Integration with more health providers
- AI-powered health insights

### Technical Improvements
- Performance optimization
- Enhanced security measures
- Better error handling
- Improved user experience 