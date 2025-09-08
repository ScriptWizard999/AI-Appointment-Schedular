# AI Medical Appointment Scheduler

This project is an AI-powered appointment scheduling system that simulates how clinics manage bookings.  
It identifies whether a patient is new or returning, assigns appointment durations accordingly, handles slot conflicts,  
logs confirmed bookings to Excel, and sends automated confirmation and reminder emails.  
The application is built with **Python**, **LangGraph**, and **Streamlit**, using synthetic patient and doctor data.  

---

## Features
- **Patient Lookup**: Detects new vs. returning patients from a synthetic CSV database.
- **Smart Scheduling**: Assigns 60 minutes for new patients, 30 minutes for returning ones.
- **Slot Management**: Validates requested slots and suggests the next available options if a conflict occurs.
- **Appointment Logging**: Records all confirmed bookings into an Excel file (`appointments_log.xlsx`).
- **Email Automation**: Sends confirmation emails with intake forms and appointment details, plus 3 automated reminders.
- **Interactive UI**: Streamlit-based chatbot interface for easy demo and testing.

---

## Setup Instructions

### Prerequisites
- Python 3.10 or higher
- Gmail account with App Password enabled for SMTP (see "Email Setup")

### Installation
1. Clone or download this repository:
   ```bash
   git clone https://github.com/<your-username>/ai-medical-scheduler.git
   cd ai-medical-scheduler
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. (Optional) Verify synthetic data:
   - `patients.csv` will be auto-generated with 50 synthetic patients.
   - `doctor_schedule.xlsx` will be auto-generated with a week's schedule of available/unavailable slots.

---

## Email Setup (Important)

This project uses Gmail SMTP to send confirmation and reminder emails.  
You **must** replace the placeholder values in `agent.py` with your own Gmail address and App Password:

```python
sender_email="your_email@gmail.com"
sender_pass="your_generated_app_password"
```

### How to generate an App Password:
1. Enable **2-Step Verification** in your Google Account.  
2. Go to: **Google Account > Security > App Passwords**.  
3. Choose "Mail" as the app and "Windows" (or another option) as the device.  
4. Copy the 16-character password generated and use it as your `sender_pass`.  

---

## Running the Application

1. Start the Streamlit app:
   ```bash
   streamlit run agent.py
   ```

2. Follow the chatbot prompts:
   - Enter patient info: `[Name], YYYY-MM-DD`
   - Provide booking details: `email@example.com, YYYY-MM-DD, HH:MM`

3. The agent will:
   - Identify patient type (new/returning)  
   - Book or suggest available slots  
   - Confirm the appointment  
   - Send confirmation + intake form via email  
   - Schedule 3 automated reminder emails  

---

## Example Workflow
1. User: `John Doe, 1980-05-15`  
2. Agent: Detects patient, assigns 30-minute slot (returning patient).  
3. User: `john.doe@example.com, 2025-09-10, 10:00`  
4. Agent: Books appointment, logs details, sends confirmation + reminders.  

---

## Notes
- Ensure Gmail App Password is configured correctly, otherwise email features will fail.  
- If the intake form PDF is missing, the email will still be sent (without attachment).  
- This project is for educational/demo purposes and uses synthetic data only.  

