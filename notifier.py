import os
import time
import json
import logging
import smtplib
import sys
from email.message import EmailMessage
from selenium import webdriver
from selenium.webdriver.common.by import By
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Load environment variables
load_dotenv()
SENDER_EMAIL = os.getenv("EMAIL_USER")
SENDER_PASSWORD = os.getenv("EMAIL_PASS")
RECEIVER_EMAIL = os.getenv("EMAIL_RECEIVER")

if not all([SENDER_EMAIL, SENDER_PASSWORD, RECEIVER_EMAIL]):
    logging.error("Missing environment variables in the .env file")
    exit(1)

# Configure Selenium
options = webdriver.ChromeOptions()
options.add_argument("--headless")  # Run in headless mode
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(options=options)

URL = "https://hackerone.com/directory/programs?order_direction=DESC&order_field=launched_at"
XPATH_BASE = "/html/body/div[2]/div/div/main/div/div[2]/div/div[2]/div/div/div/div/table/tbody/tr[{}]/td[1]/div/div[2]/div[1]/div/span/strong/span/a"

LATEST_PROGRAM_FILE = "latest_program.json"


def load_last_program():
    """Load the last detected program from a JSON file."""
    if os.path.exists(LATEST_PROGRAM_FILE):
        try:
            with open(LATEST_PROGRAM_FILE, "r") as f:
                data = json.load(f)
                return data.get("latest_program")
        except (json.JSONDecodeError, FileNotFoundError):
            return None
    return None


def save_last_program(program_name):
    """Save the last detected program into a JSON file."""
    with open(LATEST_PROGRAM_FILE, "w") as f:
        json.dump({"latest_program": program_name}, f)


def send_email(subject, body):
    """Send an email notification."""
    try:
        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = SENDER_EMAIL
        message["To"] = RECEIVER_EMAIL
        message.set_content(body, subtype="html")

        with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
            smtp.starttls()
            smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
            smtp.send_message(message)
            logging.info("Notification email sent successfully.")
    except Exception as e:
        logging.error(f"Error sending email: {e}")


# Main Monitoring Logic
try:
    driver.get(URL)
    time.sleep(5)  # Wait for page to fully load

    try:
        first_program_element = driver.find_element(By.XPATH, XPATH_BASE.format(1))
        first_program_name = first_program_element.text.strip()
        first_program_link = first_program_element.get_attribute("href")

        last_program = load_last_program()

        if last_program is None:
            last_program = first_program_name
            logging.info(f"Detected current program: {first_program_name}")
            save_last_program(last_program)
            send_email(
                "Bug Hunter jf0x0r, First program detected",
                f"""<h1>✨ New program detected on HackerOne ✨</h1>
                <p>Hello 👋 bug hunter!</p>
                <p>A new program has been detected on HackerOne:</p>
                <ul>
                    <li><strong>Program:</strong> {first_program_name}</li>
                    <li><strong>Link:</strong> <a href="{first_program_link}">{first_program_link}</a></li>
                </ul>
                <p>Good luck and happy hunting! 🐞</p>"""
            )
        elif first_program_name != last_program:
            logging.info(f"New program detected: {first_program_name}")
            save_last_program(first_program_name)
            send_email(
                "Bug Hunter jf0x0r, New Program on HackerOne!",
                f"""<h1>🚀 New Program Alert on HackerOne!</h1>
                <p>Hey Hacker! 👨‍💻</p>
                <p>A new program has just launched:</p>
                <ul>
                    <li><strong>Program:</strong> {first_program_name}</li>
                    <li><strong>Link:</strong> <a href="{first_program_link}">{first_program_link}</a></li>
                </ul>
                <p>Grab your tools and go wild! ⚔️</p>"""
            )
        else:
            logging.info("No new program detected.")
            send_email(
                "Bug Hunter jf0x0r, No updates yet",
                f"""<h1>No new updates 😴</h1>
                <p>Hey Hacker,</p>
                <p>Currently, there are no new programs available on HackerOne.</p>
                <p>Keep calm and check back later! 💻</p>"""
            )

    except Exception as e:
        logging.error(f"Error extracting program info: {e}")

finally:
    driver.quit()
