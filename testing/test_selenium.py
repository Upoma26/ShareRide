import threading
import unittest
from werkzeug.serving import make_server
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from app import create_app


class ShareRideSeleniumTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.port = 5002
        cls.base_url = f"http://127.0.0.1:{cls.port}"
        cls.server = make_server("127.0.0.1", cls.port, cls.app)
        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()

        opts = Options()
        opts.add_argument("--headless=new")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--window-size=1280,800")
        cls.driver = webdriver.Edge(options=opts)
        cls.driver.implicitly_wait(5)

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "driver"):
            cls.driver.quit()
        if hasattr(cls, "server"):
            cls.server.shutdown()

    def setUp(self):
        # Ensure clean logged-out state before each test
        self.driver.get(f"{self.base_url}/logout")

    def test_01_public_pages(self):
        """TC-01/02: Test public home and about pages load properly."""
        self.driver.get(f"{self.base_url}/")
        self.assertIn("ShareRide", self.driver.title)
        self.assertIn("Share a ride", self.driver.page_source)

        self.driver.get(f"{self.base_url}/about")
        self.assertIn("About", self.driver.title)
        self.assertIn("How it works", self.driver.page_source)

    def test_02_invalid_login(self):
        """TC-09: Test login failure with incorrect credentials."""
        self.driver.get(f"{self.base_url}/login")
        self.driver.find_element(By.NAME, "phone").send_keys("01700000011")
        self.driver.find_element(By.NAME, "password").send_keys("wrongpassword")
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

        WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "alert-danger"))
        )
        self.assertIn("Wrong phone number or password", self.driver.page_source)

    def test_03_passenger_login_and_logout(self):
        """TC-07: Test passenger login and logout session management."""
        self.driver.get(f"{self.base_url}/login")
        self.driver.find_element(By.NAME, "phone").send_keys("01700000011")
        self.driver.find_element(By.NAME, "password").send_keys("demo1234")
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

        WebDriverWait(self.driver, 5).until(
            EC.url_contains("/dashboard")
        )
        self.assertIn("Ayesha Siddiqua", self.driver.page_source)

        self.driver.get(f"{self.base_url}/logout")
        WebDriverWait(self.driver, 5).until(
            EC.url_contains("/login")
        )
        self.assertIn("Sign in", self.driver.title)

    def test_04_ride_search(self):
        """TC-13/15: Test ride search API and results display."""
        self.driver.get(f"{self.base_url}/rides/search?pickup=Mohakhali&destination=Savar")
        self.assertIn("Find a ride", self.driver.page_source)
        self.assertIn("Mohakhali", self.driver.page_source)

    def test_05_driver_dashboard(self):
        """TC-36: Test driver login and provider dashboard view."""
        self.driver.get(f"{self.base_url}/login")
        self.driver.find_element(By.NAME, "phone").send_keys("01700000001")
        self.driver.find_element(By.NAME, "password").send_keys("demo1234")
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

        WebDriverWait(self.driver, 5).until(
            EC.url_contains("/provider/dashboard")
        )
        self.assertIn("Total rides", self.driver.page_source)
        self.assertIn("Earnings", self.driver.page_source)

    def test_06_admin_overview(self):
        """TC-49: Test admin login and administrative overview panels."""
        self.driver.get(f"{self.base_url}/login")
        self.driver.find_element(By.NAME, "phone").send_keys("01700000000")
        self.driver.find_element(By.NAME, "password").send_keys("demo1234")
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

        WebDriverWait(self.driver, 5).until(
            EC.url_contains("/admin")
        )
        self.assertIn("Admin overview", self.driver.page_source)
        self.assertIn("Review NIDs", self.driver.page_source)

    def test_07_chat_api_and_ui(self):
        """TC-29/30: Test ride chat interface and messages polling endpoint."""
        # Login as passenger member of ride 4
        self.driver.get(f"{self.base_url}/login")
        self.driver.find_element(By.NAME, "phone").send_keys("01700000011")
        self.driver.find_element(By.NAME, "password").send_keys("demo1234")
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

        WebDriverWait(self.driver, 5).until(
            EC.url_contains("/dashboard")
        )

        # Open chat room for ride 4
        self.driver.get(f"{self.base_url}/chat/ride/4")
        self.assertIn("Ride chat", self.driver.page_source)

        # Test JSON polling API directly through the browser session
        poll_result = self.driver.execute_async_script("""
            var done = arguments[arguments.length - 1];
            fetch('/chat/ride/4/messages')
                .then(res => res.json())
                .then(data => done(data))
                .catch(err => done({error: err.toString()}));
        """)
        self.assertIn("messages", poll_result)
        self.assertIsInstance(poll_result["messages"], list)


if __name__ == "__main__":
    unittest.main()
