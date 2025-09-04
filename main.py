from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, StaleElementReferenceException
from selenium.webdriver.edge.service import Service
import time
import json


class EasyApplyLinkedin:

    def __init__(self, data):
        """Parameter initialization"""

        self.email = data['email']
        self.password = data['password']
        self.keywords = data['keywords']
        self.location = data['location']
        self.phone = data.get('phone', "")  # optional autofill
        edge_service = Service(data['driver_path'])
        self.driver = webdriver.Edge(service=edge_service)

    def login_linkedin(self):
        """Login to LinkedIn"""

        self.driver.get("https://www.linkedin.com/login")
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.NAME, 'session_key'))
        )
        login_email = self.driver.find_element(By.NAME, 'session_key')
        login_email.clear()
        login_email.send_keys(self.email)
        login_pass = self.driver.find_element(By.NAME, 'session_password')
        login_pass.clear()
        login_pass.send_keys(self.password)
        login_pass.send_keys(Keys.RETURN)
        print("🔑 Logged into LinkedIn.")

    def handle_easy_apply(self, job_title):
        """Handles Easy Apply modal including multi-step forms"""

        try:
            while True:
                # Autofill phone if needed
                try:
                    phone_field = self.driver.find_element(By.CSS_SELECTOR, "input[id*='phoneNumber']")
                    if phone_field.get_attribute("value") == "" and self.phone:
                        phone_field.send_keys(self.phone)
                        print("📱 Filled phone number.")
                except NoSuchElementException:
                    pass

                # Submit button
                try:
                    submit_btn = self.driver.find_element(By.XPATH, "//button[@aria-label='Submit application']")
                    submit_btn.click()
                    print(f"✅ Successfully applied to: {job_title}")
                    break
                except NoSuchElementException:
                    pass

                # Next button (new robust selector)
                try:
                    next_btn = self.driver.find_element(
                        By.CSS_SELECTOR,
                        "button[data-easy-apply-next-button], button[data-live-test-easy-apply-next-button]"
                    )
                    if next_btn.is_enabled():
                        next_btn.click()
                        print("➡️ Clicked Next step...")
                        time.sleep(2)
                        continue
                except NoSuchElementException:
                    pass

                # Review button
                try:
                    review_btn = self.driver.find_element(By.XPATH, "//button[@aria-label='Review your application']")
                    review_btn.click()
                    print("🔍 Reviewing application...")
                    time.sleep(2)
                    continue
                except NoSuchElementException:
                    pass

                print("⚠️ Unknown step. Closing modal.")
                break

            # Close modal
            try:
                dismiss_btn = WebDriverWait(self.driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Dismiss']"))
                )
                dismiss_btn.click()
                time.sleep(1)
            except NoSuchElementException:
                pass

        except Exception:
            print(f"❌ Error during Easy Apply for: {job_title}")

    def job_search_and_apply(self):
        """Search jobs and apply"""

        self.driver.get("https://www.linkedin.com/jobs/")
        WebDriverWait(self.driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[aria-label='Search by title, skill, or company']"))
        )

        # Enter search keywords
        search_keywords = self.driver.find_element(By.CSS_SELECTOR, "input[aria-label='Search by title, skill, or company']")
        search_keywords.clear()
        search_keywords.send_keys(self.keywords)
        search_keywords.send_keys(Keys.RETURN)
        time.sleep(5)

        # Enter location
        try:
            location_input = self.driver.find_element(By.CSS_SELECTOR, "input[aria-label='City, state, or zip code']")
            location_input.clear()
            location_input.send_keys(self.location)
            location_input.send_keys(Keys.RETURN)
            time.sleep(5)
        except NoSuchElementException:
            pass

        # Apply Easy Apply filter
        try:
            easy_apply_filter = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@aria-label, 'Easy Apply filter.')]"))
            )
            easy_apply_filter.click()
            time.sleep(5)
        except NoSuchElementException:
            print("⚠️ Easy Apply filter not found, continuing without filter.")

        # Loop through pages
        while True:
            try:
                WebDriverWait(self.driver, 30).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "ul.semantic-search-results-list > li"))
                )
                job_cards = self.driver.find_elements(By.CSS_SELECTOR, "ul.semantic-search-results-list > li")
            except Exception:
                print("❌ No job cards found.")
                break

            for i in range(len(job_cards)):
                try:
                    job_cards = self.driver.find_elements(By.CSS_SELECTOR, "ul.semantic-search-results-list > li")
                    job_card = job_cards[i]

                    # Only process job cards that have a job link (skip empty/generic occludable areas)
                    try:
                        job_link = job_card.find_element(By.CSS_SELECTOR, "a.job-card-job-posting-card-wrapper__card-link")
                    except NoSuchElementException:
                        continue

                    self.driver.execute_script("arguments[0].scrollIntoView(true);", job_card)
                    job_card.click()
                    time.sleep(2)

                    # Wait for job details pane to load
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div.jobs-details__main-content"))
                    )

                    # Find Easy Apply button inside job details pane (new selector)
                    try:
                        easy_apply_btn = self.driver.find_element(
                            By.CSS_SELECTOR,
                            "div.jobs-s-apply button.jobs-apply-button"
                        )
                        # Confirm it's the Easy Apply button by text
                        if "Easy Apply" in easy_apply_btn.text:
                            self.driver.execute_script("arguments[0].click();", easy_apply_btn)
                            time.sleep(2)
                            self.handle_easy_apply(job_card.text.split("\n")[0])
                        else:
                            print(f"❌ No Easy Apply button for: {job_card.text.split(chr(10))[0]}")
                            continue
                    except NoSuchElementException:
                        print(f"❌ No Easy Apply button for: {job_card.text.split(chr(10))[0]}")
                        continue

                except StaleElementReferenceException:
                    print("♻️ Skipping stale job card.")
                    continue
                except Exception as e:
                    print("⚠️ Error processing job:", e)

                time.sleep(2)

            # Next page
            try:
                next_page_btn = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Next']"))
                )
                self.driver.execute_script("arguments[0].scrollIntoView(true);", next_page_btn)
                next_page_btn.click()
                time.sleep(5)
            except (NoSuchElementException, ElementClickInterceptedException):
                print("✅ No more pages available.")
                break

    def close_session(self):
        """Close session"""
        print('👋 End of the session, see you later!')
        self.driver.quit()

    def apply(self):
        """Main function"""
        self.driver.maximize_window()
        self.login_linkedin()
        time.sleep(5)
        self.job_search_and_apply()
        self.close_session()


if __name__ == '__main__':

    with open('config.json') as config_file:
        data = json.load(config_file)

    bot = EasyApplyLinkedin(data)
    bot.apply()
