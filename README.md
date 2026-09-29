# UCMS Login Automation Framework

Professional, beginner-friendly automation suite for the **UCMS Login & Dashboard** modules  
using **Python + Playwright + Pytest + Page Object Model (POM)**.

Application under test:  
https://ucms.dev.geniussystems.com.np/login

---

## Project Structure

```
ucms_login_automation/
├── config/
│   └── config.py          # Central configuration (reads .env)
├── pages/
│   ├── login_page.py      # Login page object
│   └── dashboard_page.py  # Dashboard + logout helpers
├── tests/
│   ├── conftest.py        # Fixtures & failure screenshot hook
│   └── test_login.py      # All TC_LOGIN_* and TC_DASHBOARD_* tests
├── utils/
│   └── helpers.py         # Screenshot, clear session, etc.
├── reports/               # Generated HTML reports (auto-created)
├── screenshots/           # Failure screenshots (auto-created)
├── .env.example           # Template for credentials
├── pytest.ini             # Pytest configuration
├── requirements.txt
└── README.md
```

---

## Prerequisites

- Python 3.10+
- pip
- Git (optional)

---

## Setup (one-time)

```bash
# 1. Clone / navigate into the project
cd ucms_login_automation

# 2. Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate          # Linux / macOS
# venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install Playwright browsers
playwright install chromium

# 5. Configure credentials
cp .env.example .env
# Edit .env and set VALID_USERNAME / VALID_PASSWORD if different from defaults
```

---

## Running the tests

```bash
# Run the full Login + Dashboard suite
pytest

# Run only smoke tests
pytest -m smoke

# Run only login tests
pytest -m login

# Run a single test case
pytest tests/test_login.py::test_TC_LOGIN_001_login_with_valid_credentials

# Run headed (see the browser)
HEADLESS=false pytest

# Generate HTML report only (already configured in pytest.ini)
pytest --html=reports/report.html --self-contained-html
```

After the run open:

```
reports/report.html
```

Screenshots of failed tests are saved under `screenshots/`.


## Important Notes for Beginners

1. **Never hard-code passwords** – they live in `.env` (which is git-ignored).
2. **Locators** use Playwright’s recommended methods (`get_by_role`, `get_by_label`, `get_by_text`).  
   If a locator breaks after a UI change, open the page in headed mode and use Playwright Inspector:
   ```bash
   PWDEBUG=1 pytest tests/test_login.py::test_TC_LOGIN_001_login_with_valid_credentials
   ```
3. **Session behaviour** – After login the application restores the last visited page (Dashboard, Network Explorer, etc.). The tests only assert that the user is authenticated and is **not** on the login page.
4. **Error messages** – Some validation texts are application-specific. If an assertion fails because of wording differences, update the expected text in `login_page.py` after inspecting the real UI.

---

## Adding New Tests

1. Create a new method in the appropriate Page Object (`pages/`).
2. Write the test in `tests/test_*.py` using the existing fixtures.
3. Keep the naming convention `test_TC_XXX_description`.

---

## Troubleshooting

| Problem                        | Solution                                              |
|--------------------------------|-------------------------------------------------------|
| `playwright not found`         | Run `playwright install chromium`                     |
| Credentials rejected           | Check `.env` values                                   |
| Locator timeout                | Run with `PWDEBUG=1` and inspect the element          |
| 403 / network error            | Confirm the environment can reach the application URL |

---

