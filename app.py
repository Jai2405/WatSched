from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

subject = input("Enter subject (e.g., STAT): ").strip()
course_number = input("Enter course number (e.g., 230): ").strip()

# Set up headless Chrome (or remove headless if you want to see the browser)
options = webdriver.ChromeOptions()
# options.add_argument('--headless')  # Uncomment this if you want it headless
options.add_argument('--disable-gpu')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

# Launch driver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
wait = WebDriverWait(driver, 10)

try:
    # Open the page and switch to the "select" iframe
    driver.get("https://cs.uwaterloo.ca/cscf/teaching/schedule/expert")
    wait.until(EC.frame_to_be_available_and_switch_to_it("select"))

    # Select subject from dropdown (case-insensitive match)
    dropdown = Select(wait.until(EC.presence_of_element_located((By.NAME, "subject"))))
    subject_normalized = subject.strip().lower()
    match = next((opt.text for opt in dropdown.options if opt.text.strip().lower().startswith(subject_normalized)), None)

    if not match:
        print(f"❌ Could not find subject '{subject}' in dropdown.")
    else:
        dropdown.select_by_visible_text(match)

        # Enter course number
        course_input = wait.until(EC.presence_of_element_located((By.NAME, "cournum")))
        course_input.clear()
        course_input.send_keys(course_number)

        # Click submit
        view_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@value='View Class Schedules']")))
        view_btn.click()

        # Switch to results frame and print the content
        driver.switch_to.default_content()
        wait.until(EC.frame_to_be_available_and_switch_to_it("results"))
        time.sleep(2)
        print("\n✅ Results loaded:\n")
        print(driver.find_element(By.TAG_NAME, "body").text)

except Exception as e:
    print("❌ Error:", e)

finally:
    driver.quit()
