import pandas as pd
from faker import Faker
import random
import os
import datetime
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage
import smtplib
import streamlit as st
from email.message import EmailMessage
import time


# --- Data Handling Functions ---
def generate_patient_data(num_patients=50, filename="patients.csv"):
    if not os.path.exists(filename):
        fake = Faker()
        patients_data = []
        for i in range(1, num_patients + 1):
            is_returning = random.choice([True, False, False])
            patients_data.append({
                'patient_id': f'P{i:03d}',
                'name': fake.name(),
                'date_of_birth': fake.date_of_birth(minimum_age=18, maximum_age=90).strftime('%Y-%m-%d'),
                'is_returning': is_returning
            })
        df = pd.DataFrame(patients_data)
        df.to_csv(filename, index=False)
        print(f"[INFO] Generated synthetic patient database: {filename}")

def generate_doctor_schedule(filename="doctor_schedule.xlsx"):
    if not os.path.exists(filename):
        start_date = datetime.date.today() + datetime.timedelta(days=1)
        dates = pd.date_range(start_date, periods=7)
        times = [f'{h:02d}:00' for h in range(9, 17)]
        
        schedule_data = []
        for date in dates:
            for time in times:
                is_available = random.choice([True, False, False]) 
                schedule_data.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'time': time,
                    'is_available': is_available
                })
        df = pd.DataFrame(schedule_data)
        df.to_excel(filename, index=False)
        print(f"[INFO] Generated mock doctor schedule: {filename}")

def find_patient(name):
    try:
        df = pd.read_csv("patients.csv")
        patient_record = df[df['name'].str.lower() == name.lower()]
        if not patient_record.empty:
            is_returning = patient_record.iloc[0]['is_returning']
            return True, is_returning
        return False, None
    except FileNotFoundError:
        return False, None

def book_appointment(date, time):
    try:
        df = pd.read_excel("doctor_schedule.xlsx")
        if not df[(df['date'] == date) & (df['time'] == time) & (df['is_available'] == True)].empty:
            df.loc[(df['date'] == date) & (df['time'] == time), 'is_available'] = False
            df.to_excel("doctor_schedule.xlsx", index=False)
            return True
        return False
    except FileNotFoundError:
        return False

def export_to_excel(patient_details, filename="appointments_log.xlsx"):
    df_new = pd.DataFrame([patient_details])
    if os.path.exists(filename):
        try:
            df_old = pd.read_excel(filename)
            df_combined = pd.concat([df_old, df_new], ignore_index=True)
        except Exception: 
            df_combined = df_new
    else:
        df_combined = df_new
    
    df_combined.to_excel(filename, index=False)
    print(f"[INFO] Appointment details logged to {filename}")



# --- Email + Reminder --- Sends the intake form as a real email with appointment details.



def send_email_with_form(to_email, patient_name,
                         sender_email="YourEmail@gmail.com",  #---------->>>> Replace your email here
                         sender_pass="Your_App_PassWord",      #---------->>>> Replace your App Password Here
                         form_path="New Patient Intake Form.pdf",
                         appointment_date=None,
                         appointment_time=None):

    # Build body with appointment info
    appointment_info = ""
    if appointment_date and appointment_time:
        appointment_info = f"\n📅 Date: {appointment_date}\n⏰ Time: {appointment_time}\n"

    msg = EmailMessage()
    msg["Subject"] = "Your Appointment Confirmation & Intake Form"
    msg["From"] = sender_email
    msg["To"] = to_email

    msg.set_content(
        f"Hi {patient_name},\n\n"
        "Your appointment has been confirmed." +
        appointment_info +
        "\nPlease find attached the intake form and return it before your visit.\n\n"
        "Regards,\nRagaAI Scheduling Agent"
    )

    # Attach PDF
    try:
        with open(form_path, "rb") as f:
            msg.add_attachment(
                f.read(),
                maintype="application",
                subtype="pdf",
                filename="New Patient Intake Form.pdf"
            )
    except FileNotFoundError:
        print("[WARNING] Intake form file not found. Email will be sent without attachment.")

    # Send email
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, sender_pass)
            server.send_message(msg)
        print(f"📧 Email sent successfully to {to_email} with appointment details")
    except Exception as e:
        print(f"⚠️ Failed to send email: {e}")


# Sends a reminder email to the patient.
# reminder_number = 1, 2, or 3


def send_reminder_email(to_email, patient_name, reminder_number,
                        sender_email="YourEmail@gmail.com", #---------->>>> Replace your email here
                        sender_pass="Your_App_PassWord"):    #---------->>>> Replace your App Password Here

    subjects = {
        1: "Appointment Reminder",
        2: "Reminder: Intake Form Pending",
        3: "Final Reminder: Confirm Your Appointment"
    }

    bodies = {
        1: f"Hi {patient_name},\n\nThis is a reminder of your upcoming appointment.\n\nRegards,\nClinic",
        2: f"Hi {patient_name},\n\nPlease remember to complete and return your intake form before your visit.\n\nRegards,\nClinic",
        3: f"Hi {patient_name},\n\nPlease confirm if you are still attending your appointment. If not, reply with the reason for cancellation.\n\nRegards,\nClinic"
    }

    msg = EmailMessage()
    msg["Subject"] = subjects[reminder_number]
    msg["From"] = sender_email
    msg["To"] = to_email
    msg.set_content(bodies[reminder_number])

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, sender_pass)
            server.send_message(msg)
        print(f"📧 Reminder {reminder_number} email sent to {to_email}")
    except Exception as e:
        print(f"⚠️ Failed to send reminder {reminder_number}: {e}")




# --- LangGraph Agent Architecture ---
class GraphState(TypedDict):
    name: str | None
    date_of_birth: str | None
    patient_type: str | None
    appointment_date: str | None
    appointment_time: str | None
    appointment_duration: int | None
    email: str | None
    is_booked: bool | None
    messages: Annotated[list[BaseMessage], lambda x, y: x + y]



# --- Nodes ---
def patient_lookup_node(state: GraphState):
    user_input = state["messages"][-1].content.strip()
    try:
        parts = [p.strip() for p in user_input.split(",")]
        if len(parts) != 2:
            raise ValueError("Invalid format")

        name, dob_str = parts[0], parts[1]
        datetime.datetime.strptime(dob_str, "%Y-%m-%d")  # validate DOB

        found, is_returning = find_patient(name)

        if found:
            patient_type = "returning" if is_returning else "new"
            duration = 30 if is_returning else 60
            message = (
                f"Hello {name}, you are a {patient_type} patient. "
                f"Your appointment will be {duration} minutes.\n\n"
                "📧 Please provide your email, appointment date, and time like: `email@example.com, YYYY-MM-DD, HH:MM`"
            )
            return {"name": name, "date_of_birth": dob_str, "patient_type": patient_type,
                    "appointment_duration": duration,
                    "messages": [HumanMessage(content=message)],
                    "valid_lookup": True}
        else:
            message = (
                f"Hi {name}, no record found. We’ll register you as a new patient (60 minutes).\n\n"
                "📧 Please provide your email, appointment date, and time like: `email@example.com, YYYY-MM-DD, HH:MM`"
            )
            return {"name": name, "date_of_birth": dob_str, "patient_type": "new",
                    "appointment_duration": 60,
                    "messages": [HumanMessage(content=message)],
                    "valid_lookup": True}

    except Exception:
        return {"messages": [HumanMessage(content="⚠️ Format: `[Name], YYYY-MM-DD`")],
                "valid_lookup": False}

    


def smart_scheduling_node(state: GraphState):
    user_input = state["messages"][-1].content.strip()
    parts = [p.strip() for p in user_input.split(",")]

    if len(parts) < 3:
        return {
            "messages": [HumanMessage(content="⚠️ Format: `email@example.com, YYYY-MM-DD, HH:MM`")],
            "valid_schedule": False
        }

    email_str, date_str, time_str = parts[0], parts[1], parts[2]
    state["email"] = email_str

    # validate date + time
    try:
        datetime.datetime.strptime(date_str, "%Y-%m-%d")
        datetime.datetime.strptime(time_str, "%H:%M")
    except ValueError:
        return {
            "messages": [HumanMessage(content="⚠️ Invalid date/time format. Use `YYYY-MM-DD, HH:MM`.")],
            "valid_schedule": False
        }

    # try booking
    if book_appointment(date_str, time_str):
        return {
            "appointment_date": date_str,
            "appointment_time": time_str,
            "is_booked": True,
            "valid_schedule": True,
            "messages": [
                HumanMessage(content=f"✅ Appointment scheduled for {date_str} at {time_str}.")
            ]
        }
    else:
        df = pd.read_excel("doctor_schedule.xlsx")
        available = df[df["is_available"] == True].head(3)
        if not available.empty:
            suggestions = "\n".join([f"{row['date']} at {row['time']}" for _, row in available.iterrows()])
            return {
                "messages": [HumanMessage(content=f"❌ Slot unavailable. Next options:\n{suggestions}\nPick one (e.g. `2025-09-11, 11:00`).")],
                "is_booked": False,
                "valid_schedule": False
            }
        return {
            "messages": [HumanMessage(content="❌ No slots available.")],
            "valid_schedule": False
        }

    


    
def confirmation_node(state: GraphState):
    """Finalizes the appointment: logs, emails intake form, and sends reminders."""

    # --- Log appointment ---
    patient_details = {
        'name': state.get('name'),
        'patient_type': state.get('patient_type'),
        'appointment_date': state.get('appointment_date'),
        'appointment_time': state.get('appointment_time'),
        'duration': state.get('appointment_duration'),
        'email': state.get('email')
    }
    export_to_excel(patient_details)

    # --- Email intake form + reminders ---
    email = state.get("email")
    patient_name = state.get("name") or "Patient"
    print("DEBUG STATE:", state)

    if email:
        send_email_with_form(
            to_email=email,
            patient_name=patient_name,
            sender_email="YourEmail@gmail.com",   #---------->>>> Replace your email here
            sender_pass="Your_App_PassWord",       #---------->>>> Replace your App Password Here
            appointment_date=state.get("appointment_date"),
            appointment_time=state.get("appointment_time")
        )

        for i in range(1, 4):
            send_reminder_email(
                to_email=email,
                patient_name=patient_name,
                reminder_number=i,
                sender_email="YourEmail@gmail.com",   #---------->>>> Replace your email here
                sender_pass="Your_App_PassWord"        #---------->>>> Replace your App Password Here
            )

    return {
        "messages": [
            HumanMessage(content=f"✅ Appointment confirmed for {patient_name}. Intake form and reminders sent via email.")
        ]
    }


def main():
    st.title("🩺 Your AI Appointment Scheduler")

    # initialize session state
    if "state" not in st.session_state:
        generate_patient_data()
        generate_doctor_schedule()
        st.session_state.state = {
            "messages": [HumanMessage(content="Enter your name and DOB: `[Name], YYYY-MM-DD`")]
        }
        st.session_state.current_node = "patient_lookup"

    # display assistant’s last message
    st.write("**Assistant:**", st.session_state.state["messages"][-1].content)

    # input box for user
    user_input = st.text_input("You:", key="user_input")

    if st.button("Send"):
        if user_input.strip():
            st.session_state.state["messages"].append(HumanMessage(content=user_input))

            response = None  # default

            if st.session_state.current_node == "patient_lookup":
                response = patient_lookup_node(st.session_state.state)
                  # only move forward if lookup was valid
                if response.get("valid_lookup"):
                   st.session_state.current_node = "smart_scheduling"


            elif st.session_state.current_node == "smart_scheduling":
                sched_response = smart_scheduling_node(st.session_state.state)

                # merge scheduling response into state
                if sched_response:
                    for k, v in sched_response.items():
                        if k == "messages":
                            st.session_state.state["messages"].extend(v)
                        else:
                            st.session_state.state[k] = v

                # only confirm if booking was valid and successful
                if sched_response and sched_response.get("valid_schedule") and sched_response.get("is_booked"):
                    confirm_response = confirmation_node(st.session_state.state)
                    if confirm_response:
                        for k, v in confirm_response.items():
                            if k == "messages":
                                st.session_state.state["messages"].extend(v)
                            else:
                                st.session_state.state[k] = v
                    st.session_state.current_node = "done"


            # merge response from patient_lookup
            if response:
                for k, v in response.items():
                    if k == "messages":
                        st.session_state.state["messages"].extend(v)
                    else:
                        st.session_state.state[k] = v

            st.rerun()

    # display full conversation
    st.subheader("Conversation")
    for msg in st.session_state.state["messages"]:
        st.write(f"{msg.type.capitalize()}: {msg.content}")


if __name__ == "__main__":
    main()
