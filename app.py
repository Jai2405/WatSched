from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
import re
import json
import time

def split_days(day_str):
    day_str = day_str.upper()
    days = []
    i = 0
    while i < len(day_str):
        if day_str[i] == 'T' and i + 1 < len(day_str) and day_str[i + 1] == 'H':
            days.append('TH')
            i += 2
        else:
            days.append(day_str[i])
            i += 1
    return days

class CourseScheduleScraper:
    def __init__(self, subject, course_number):
        self.subject = subject.strip()
        self.course_number = course_number.strip()
        self.options = webdriver.ChromeOptions()
        self.options.add_argument('--headless')
        self.options.add_argument('--disable-gpu')
        self.options.add_argument('--no-sandbox')
        self.options.add_argument('--disable-dev-shm-usage')
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.options)
        self.wait = WebDriverWait(self.driver, 10)

    def scrape_schedule(self):
        try:
            self.driver.get("https://cs.uwaterloo.ca/cscf/teaching/schedule/expert")
            self.wait.until(EC.frame_to_be_available_and_switch_to_it("select"))

            # Select subject from dropdown
            dropdown = Select(self.wait.until(EC.presence_of_element_located((By.NAME, "subject"))))
            subject_normalized = self.subject.lower()
            match = next((opt.text for opt in dropdown.options if opt.text.strip().lower().startswith(subject_normalized)), None)

            if not match:
                print(f"❌ Could not find subject '{self.subject}' in dropdown.")
                return []

            dropdown.select_by_visible_text(match)

            # Enter course number
            course_input = self.wait.until(EC.presence_of_element_located((By.NAME, "cournum")))
            course_input.clear()
            course_input.send_keys(self.course_number)

            # Submit form
            view_btn = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@value='View Class Schedules']")))
            view_btn.click()

            # Switch to results frame
            self.driver.switch_to.default_content()
            self.wait.until(EC.frame_to_be_available_and_switch_to_it("results"))
            time.sleep(2)

            # Get and parse content
            content = self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body"))).text
            class_pattern = r'(LEC|TUT) (\d{3}).*?(\d{1,2}:\d{2}-\d{1,2}:\d{2})([A-Za-z,]+)'
            matches = re.finditer(class_pattern, content)

            schedules = []
            for match in matches:
                class_type, section, time_str, days = match.groups()
                if not time_str.startswith('Reserve'):
                    schedules.append({
                        "section": f"{class_type} {section}",
                        "time": time_str,
                        "days": split_days(days.strip())
                    })

            print(f"\n✅ Results for {self.subject.upper()} {self.course_number} loaded:")
            print(content)
            return schedules

        except Exception as e:
            print(f"Error: {str(e)}")
            return []
        finally:
            self.cleanup()

    def cleanup(self):
        if self.driver:
            self.driver.quit()

def main():
    total_schedules = {}
    while True:
        subject = input("Enter subject (e.g., CS) or 'q' to quit: ").strip()
        if subject.lower() == 'q':
            break

        course_number = input("Enter course number (e.g., 246): ").strip()
        scraper = CourseScheduleScraper(subject, course_number)
        schedules = scraper.scrape_schedule()

        key = f"{subject.upper()} {course_number}"
        if schedules:
            total_schedules[key] = schedules
            print(json.dumps(schedules, indent=2))
        else:
            print(f"No schedules found for {key}")

    print("\nTOTAL RESULTS:")
    print(json.dumps(total_schedules, indent=2))

if __name__ == "__main__":
    main()
