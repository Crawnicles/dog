#!/usr/bin/env python3
"""
Watch Underdog Rescue MN and send an SMS when DOG_NAME appears.

• Polls once per CHECK_EVERY seconds.
• Exits after the first alert (systemd Restart=always will start a fresh copy next boot).
"""

import time, logging, yagmail
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager   # make sure version < 4.0.0 for Py 3.7

# ─── CONFIG ────────────────────────────────────────────────────────────────
URL           = "https://underdogrescuemn.com/adoptable-animals/adoptable-dogs-and-puppies/"
DOG_NAME      = "Buster"               # name to watch for (case-insensitive)
CHECK_EVERY   = 60                     # seconds between checks (1 minute)

SENDER_EMAIL  = "crawnicles@gmail.com"
APP_PASSWORD  = "cotsiwlshkdwwljk"     # 16-char Gmail app password — no spaces
RECIPIENT_SMS = "6056914742@vtext.com" # phone@carrier-gateway
# ───────────────────────────────────────────────────────────────────────────

logging.basicConfig(
    filename="/home/pi/dogwatch.log",   # writeable by user “pi”
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

def setup_driver() -> webdriver.Chrome:
    """Return a lightweight headless-Chrome driver."""
    opts = webdriver.ChromeOptions()
    opts.add_argument("--headless")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--blink-settings=imagesEnabled=false")  # skip images
    return webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=opts
    )

def dog_found(driver: webdriver.Chrome) -> bool:
    """Load the page and check if DOG_NAME appears in the HTML."""
    driver.get(URL)
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )
    return DOG_NAME.lower() in driver.page_source.lower()

def send_sms() -> None:
    """Send a one-line e-mail-to-SMS alert."""
    yagmail.SMTP(SENDER_EMAIL, APP_PASSWORD).send(
        to=RECIPIENT_SMS,
        subject="",
        contents=f"🐶  {DOG_NAME} is now listed on Underdog Rescue MN!"
    )
    logging.info("SMS sent!")

def monitor_site() -> None:
    driver = setup_driver()
    try:
        while True:
            try:
                if dog_found(driver):
                    logging.info("%s found – texting!", DOG_NAME)
                    send_sms()
                    break
                logging.info("Checked – no %s yet", DOG_NAME)
            except Exception:
                logging.exception("Check failed")
            time.sleep(CHECK_EVERY)
    finally:
        driver.quit()

if __name__ == "__main__":
    monitor_site()
