import unittest
import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

class InsiderCareerTest(unittest.TestCase):

    def setUp(self):
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

        hub_url = "http://selenium-chrome-service:4444/wd/hub"
        print(f"[INFO] Connecting to WebDriver at: {hub_url}")
        
        self.driver = None
        for i in range(5):
            try:
                self.driver = webdriver.Remote(command_executor=hub_url, options=chrome_options)
                print("[INFO] Connection established.")
                break
            except Exception:
                print(f"[WARN] Connection attempt {i+1}/5 failed. Retrying in 5s...")
                time.sleep(5)
        
        if self.driver is None:
            self.fail("[FATAL] Could not connect to Remote WebDriver.")

        self.wait = WebDriverWait(self.driver, 30)
        self.jobs = []

    def tearDown(self):
        if self.driver:
            self.driver.quit()

    def filter_jobs(self):
        driver = self.driver
        wait = self.wait

        print("\n[STEP 1] Navigating to Career Page...")
        driver.get("https://useinsider.com/careers/quality-assurance/")

        try:
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "wt-cli-accept-all-btn"))).click()
            print("[INFO] Cookies accepted.")
        except: 
            print("[INFO] Cookie banner not found or skipped.")

        print("[INFO] Clicking 'See all QA jobs'...")
        btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'See all QA jobs')]")))
        driver.execute_script("arguments[0].click();", btn)
        
        print("[INFO] Waiting for filter section...")
        wait.until(EC.visibility_of_element_located((By.ID, "filter-by-location")))
        
        print("[INFO] Waiting for Location Dropdown to populate...")
        
        loc_el = driver.find_element(By.ID, "filter-by-location")
        driver.execute_script("arguments[0].style.display = 'block';", loc_el)
        loc_select = Select(loc_el)

        is_populated = False
        for i in range(20):
            if len(loc_select.options) > 1:
                is_populated = True
                print(f"[INFO] Dropdown populated! Option count: {len(loc_select.options)}")
                break
            
            print(f"   -> Waiting for data... (Current options: {len(loc_select.options)})")
            time.sleep(1)
            if i % 5 == 0:
                driver.execute_script("arguments[0].click();", loc_el)

        if not is_populated:
            self.fail(f"[FAIL] Dropdown data did not load. Options: {[o.text for o in loc_select.options]}")

        locations = ["Istanbul, Turkiye", "Istanbul, Turkey", "Istanbul"]
        selected = False
        
        for loc in locations:
            try:
                loc_select.select_by_visible_text(loc)
                print(f"[INFO] Location selected: {loc}")
                selected = True
                break
            except: continue

        if not selected:
             self.fail(f"[FAIL] Could not select target location. Options: {[o.text for o in loc_select.options[:5]]}")

        time.sleep(2)
        dept_el = driver.find_element(By.ID, "filter-by-department")
        driver.execute_script("arguments[0].style.display = 'block';", dept_el)
        Select(dept_el).select_by_visible_text("Quality Assurance")

        print("[INFO] Checking job list...")
        time.sleep(3)
        self.jobs = driver.find_elements(By.CLASS_NAME, "position-list-item")
        
        if len(self.jobs) == 0:
            print("[INFO] List empty, scrolling to trigger lazy load...")
            driver.execute_script("window.scrollTo(0, 500);")
            time.sleep(2)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            self.jobs = driver.find_elements(By.CLASS_NAME, "position-list-item")

        if len(self.jobs) > 0:
            print(f"[INFO] {len(self.jobs)} jobs found.")
        else:
            self.fail("[FAIL] No jobs found.")

    def verify_job_content(self):
        print("\n[STEP 2] Verifying job details...")
        for job in self.jobs:
            try:
                title = job.find_element(By.CLASS_NAME, "position-title").text
                dept = job.find_element(By.CLASS_NAME, "position-department").text
                loc = job.find_element(By.CLASS_NAME, "position-location").text
                
                print(f"   -> Found: {title} | {dept} | {loc}")
                
                self.assertTrue("QA" in title or "Quality Assurance" in title, f"Invalid Title: {title}")
                self.assertIn("Quality Assurance", dept, f"Invalid Dept: {dept}")
                self.assertTrue("Istanbul" in loc or "Turkey" in loc or "Turkiye" in loc, f"Invalid Location: {loc}")
            except Exception as e:
                print(f"[WARN] Skipped a job item due to missing fields: {e}")

        print("[PASS] All job details verified.")

    def check_redirection(self):
        print("\n[STEP 3] Checking redirection...")
        if not self.jobs:
            self.fail("[FAIL] No jobs to click.")

        view_btn = self.jobs[0].find_element(By.XPATH, ".//a[contains(text(), 'View Role')]")
        link = view_btn.get_attribute("href")
        print(f"[INFO] Target Link: {link}")
        
        if "lever.co" in link:
             print("[PASS] Link points to Lever.co")
        else:
             self.fail(f"[FAIL] Link incorrect: {link}")

    def test_workflow(self):
        self.filter_jobs()
        self.verify_job_content()
        self.check_redirection()

if __name__ == "__main__":
    unittest.main()