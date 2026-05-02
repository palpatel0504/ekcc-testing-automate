import os
import re
import random
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


#  pytest -s --headed --browser chromium test_smoke.py
# KEEP_BROWSER_OPEN=1 pytest -s --headed --browser chromium test_smoke.py

BASE_URL = "http://13.232.66.157:3000/SignIn?Method=farmer"
MOBILE_NUMBER = "8780426019"
STEP_DELAY_MS = 1200
from datetime import datetime
from pathlib import Path

ARTIFACTS_DIR = Path(__file__).resolve().parent / "artifacts" / "error-screenshots"


def save_error_artifact(page, step_name: str = "failure") -> None:
    """Save a screenshot when the script fails."""
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    safe_step = re.sub(r"[^a-zA-Z0-9_-]+", "-", step_name)

    screenshot_path = ARTIFACTS_DIR / f"{timestamp}-{safe_step}.png"

    page.screenshot(path=str(screenshot_path), full_page=True)
    log_step(f"Saved error screenshot to: {screenshot_path}")


def fill_mobile_number(page) -> None:
    """Fill the farmer sign-in mobile number field."""
    try:
        page.get_by_label("Mobile Number").fill(MOBILE_NUMBER, timeout=5000)
        return
    except PlaywrightTimeoutError:
        pass

    page.locator("#outlined-adornment-mobile").fill(MOBILE_NUMBER)


def click_button(page, button_name: str) -> None:
    """Click a visible button by accessible name."""
    button = page.get_by_role("button", name=button_name)
    button.wait_for(state="visible", timeout=10000)
    button.click()

def handle_existing_session_popup(page) -> None:
    """Handle the 'User already logged in' popup by clicking Yes."""
    yes_button = page.locator("button.swal2-confirm", has_text="Yes").first

    try:
        yes_button.wait_for(state="visible", timeout=8000)
        pause(page, 800)
        yes_button.click()
        log_step("Clicked Yes on 'User already logged in' popup.")
        pause(page, 2500)
    except PlaywrightTimeoutError:
        log_step("'User already logged in' popup did not appear.")


def pause(page, milliseconds: int = STEP_DELAY_MS) -> None:
    """Slow the flow down a bit so the UI has time to settle."""
    page.wait_for_timeout(milliseconds)


def log_step(message: str) -> None:
    """Print progress so it is easy to see where the script is."""
    print(f"[loan-remove] {message}", flush=True)


def fetch_otp_from_toast(page) -> str:
    """Read the OTP from the success toast shown after Send OTP."""
    otp_locator = page.locator("div.Toastify__toast-body div", has_text=re.compile(r"OTP\s*=\s*\d{4,8}")).first
    otp_locator.wait_for(state="visible", timeout=20000)
    otp_text = otp_locator.inner_text().strip()
    match = re.search(r"OTP\s*=\s*(\d{4,8})", otp_text)
    if not match:
        raise RuntimeError(f"OTP toast appeared but the OTP could not be parsed from: {otp_text!r}")
    otp = match.group(1)
    log_step(f"Fetched OTP {otp}.")
    return otp


def fill_otp_inputs(page, otp: str) -> None:
    """Fill the Enter OTP inputs using the OTP extracted from the toast."""
    otp_inputs = page.locator(
        """
        input:not([type="hidden"]):not(#outlined-adornment-mobile)
        """
    ).filter(
        has_not=page.locator('[type="hidden"]')
    )

    handles = otp_inputs.element_handles()
    visible_inputs = []
    for handle in handles:
        props = handle.evaluate(
            """
            (input) => ({
              id: input.id || '',
              name: input.name || '',
              type: input.type || '',
              placeholder: input.placeholder || '',
              ariaLabel: input.getAttribute('aria-label') || '',
              autocomplete: input.autocomplete || '',
              inputMode: input.inputMode || '',
              className: input.className || '',
              maxLength: input.maxLength || 0,
              visible: !!input.offsetParent,
            })
            """
        )

        if not props["visible"]:
            continue

        attrs = " ".join(
            str(props[key]).lower()
            for key in [
                "id",
                "name",
                "type",
                "placeholder",
                "ariaLabel",
                "autocomplete",
                "inputMode",
                "className",
            ]
            if props[key]
        )

        if "mobile" in attrs or "phone" in attrs:
            continue

        if props["maxLength"] == 1 or any(
            token in attrs for token in ["otp", "one-time-code", "verification"]
        ):
            visible_inputs.append(handle)

    if not visible_inputs:
        raise RuntimeError("Could not find any visible OTP input fields.")

    if len(visible_inputs) == 1:
        visible_inputs[0].fill(otp)
        return

    for index, digit in enumerate(otp):
        if index >= len(visible_inputs):
            break
        visible_inputs[index].fill(digit)


def handle_logout_other_devices_popup(page) -> None:
    """Click Yes if the site asks to log out from other devices."""
    popup_indicators = [
        page.locator("text=User already logged in").first,
        page.locator("text=Do you want to logout from all other devices").first,
    ]

    for locator in popup_indicators:
        try:
            locator.wait_for(state="visible", timeout=5000)
            pause(page, 800)
            click_button(page, "Yes")
            pause(page, 2000)
            return
        except PlaywrightTimeoutError:
            continue


def select_pal_rakesh_patel_card(page) -> None:
    """Click the Pal Rakesh Patel / Main user card when it appears."""
    card_candidates = [
        page.locator("h6").filter(has_text=re.compile(r"^Pal Rakesh Patel$", re.IGNORECASE)).first,
        page.locator("h6").filter(has_text=re.compile(r"^Pal Rakesh Patel$")).first,
        page.locator("div").filter(
            has=page.locator("h6", has_text="Pal Rakesh Patel")
        ).filter(
            has=page.locator("h6", has_text="Main")
        ).first,
    ]

    for candidate in card_candidates:
        try:
            candidate.wait_for(state="visible", timeout=15000)
            pause(page, 1000)

            clickable_card = candidate.locator(
                "xpath=ancestor::*[contains(@class,'MuiCard-root') or contains(@class,'MuiPaper-root')][1]"
            ).first

            if clickable_card.count():
                try:
                    clickable_card.click()
                except Exception:
                    clickable_card.click(force=True)
            else:
                try:
                    candidate.click()
                except Exception:
                    candidate.click(force=True)

            pause(page, 2500)
            return
        except PlaywrightTimeoutError:
            continue

    raise RuntimeError("Could not find the 'Pal Rakesh Patel / Main' user card.")


def open_loan_section(page) -> None:
    """Click the Loan section from the left navigation."""
    loan_link = page.locator('a[href="/loan"]').filter(has_text="Loan").first
    try:
        loan_link.wait_for(state="visible", timeout=15000)
        pause(page, 1000)
        loan_link.click()
    except PlaywrightTimeoutError:
        click_button(page, "Loan")
    pause(page, 2500)


def remove_incomplete_application_if_present(page) -> None:
    """Click Remove Application when an incomplete application is shown."""
    remove_button = page.get_by_role("button", name="Remove Application").first

    try:
        remove_button.wait_for(state="visible", timeout=6000)
        pause(page, 1000)
        remove_button.click()
        log_step("Clicked Remove Application.")
        pause(page, 2500)
    except PlaywrightTimeoutError:
        log_step("No incomplete application found to remove.")


def confirm_delete_if_popup_appears(page) -> None:
    """Click Delete on the remove-application confirmation popup."""
    delete_button = page.get_by_role("button", name="Delete").first

    try:
        delete_button.wait_for(state="visible", timeout=8000)
        pause(page, 1000)
        delete_button.click()
        log_step("Clicked Delete on confirmation popup.")
        pause(page, 2500)
    except PlaywrightTimeoutError:
        log_step("Delete confirmation popup did not appear.")

def open_sign_in_page(page) -> None:
    """Open the sign-in page and wait until the mobile input is visible."""
    log_step(f"Opening {BASE_URL}")
    response = page.goto(BASE_URL, wait_until="domcontentloaded", timeout=30000)

    if response is None or not response.ok:
        status = response.status if response else "no-response"
        raise RuntimeError(f"Could not load sign-in page. Status: {status}")

    page.wait_for_load_state("networkidle", timeout=15000)
    page.locator("#outlined-adornment-mobile").wait_for(state="visible", timeout=15000)
    log_step("Sign-in page loaded.")

def select_kcc_crop_loan(page) -> None:
    """Select the KCC-Crop loan card after clicking Apply for Loan."""
    log_step("Selecting the KCC-Crop loan card.")

    kcc_crop_card = page.locator("div").filter(
        has_text=re.compile(r"KCC\s*-?\s*Crop", re.IGNORECASE)
    ).first

    try:
        kcc_crop_card.wait_for(state="visible", timeout=10000)
        select_button = kcc_crop_card.get_by_role("button", name="Select").first
    except PlaywrightTimeoutError:
        select_button = page.get_by_role("button", name="Select").first

    select_button.wait_for(state="visible", timeout=10000)
    pause(page, 1000)
    select_button.click()
    log_step("Clicked Select on the KCC-Crop loan card.")
    pause(page, 2500)
    
def skip_ekyc_popup_if_present(page) -> None:
    """Skip the eKYC popup if it appears after selecting the loan."""
    skip_button = page.locator("button.swal2-deny", has_text="Skip for now").first

    try:
        skip_button.wait_for(state="visible", timeout=8000)
        pause(page, 1000)
        skip_button.click()
        log_step("Clicked 'Skip for now' on the eKYC popup.")
        pause(page, 2500)
    except PlaywrightTimeoutError:
        log_step("eKYC popup did not appear.")

def select_pmjjby_yes(page) -> None:
    """Select Yes for 'Whether Covered under PMJJBY/PMSBY/APY'."""
    log_step("Selecting Yes for PMJJBY/PMSBY/APY.")

    yes_option = page.locator("label").filter(
        has_text=re.compile(r"^Yes$", re.IGNORECASE)
    ).first

    yes_option.wait_for(state="visible", timeout=10000)
    pause(page, 1000)
    yes_option.click()

    log_step("Selected Yes for PMJJBY/PMSBY/APY.")
    pause(page, 2000)

def select_bank_type(page) -> None:
    """Select 'Regional Rural Bank' from the Bank Type dropdown."""
    log_step("Selecting bank type: Regional Rural Bank.")

    # bank_dropdown = page.get_by_role("combobox").first
    bank_dropdown = page.get_by_role("combobox").nth(1)
    bank_dropdown.wait_for(state="visible", timeout=10000)

    pause(page, 1000)
    bank_dropdown.click()
    pause(page, 1000)

    bank_dropdown.fill("Regional Rural Bank")
# Regional Rural Bank
    option = page.get_by_role(
        "option",
        name=re.compile(r"Regional Rural Bank", re.IGNORECASE)
    ).first

    option.wait_for(state="visible", timeout=10000)
    pause(page, 500)
    option.click()

    log_step("Selected bank type.")
    pause(page, 2000)

def select_state_and_district(page, state: str, district: str) -> None:
    """
    Select State first, wait for District to refresh, then select District.
    """

    log_step(f"Selecting State: {state}")

    # ── STATE ─────────────────────────────
    state_dropdown = page.get_by_role("combobox").nth(2)

    state_dropdown.wait_for(state="visible", timeout=10000)
    pause(page, 1000)

    state_dropdown.click()
    pause(page, 1000)

    state_dropdown.fill("")
    state_dropdown.fill(state)

    state_option = page.get_by_role(
        "option",
        name=re.compile(fr"{state}", re.IGNORECASE)
    ).first

    state_option.wait_for(state="visible", timeout=10000)
    state_option.click()

    log_step(f"State selected: {state}")
    pause(page, 2000)

    district_dropdown = page.get_by_role("combobox").nth(3)
    try:
        page.wait_for_function(
            """(el) => el.value === '' || el.value.toLowerCase().includes('select')""",
            district_dropdown,
            timeout=10000
        )
    except:
        pause(page, 2000)

    log_step("District dropdown refreshed after state change")
    log_step(f"Selecting District: {district}")

    district_dropdown.click()
    pause(page, 1000)

    district_dropdown.fill("")
    district_dropdown.fill(district)

    district_option = page.get_by_role(
        "option",
        name=re.compile(fr"{district}", re.IGNORECASE)
    ).first

    district_option.wait_for(state="visible", timeout=10000)
    district_option.click()

    log_step(f"District selected: {district}")
    pause(page, 2000)


def select_state_and_district(page) -> None:
    """Select State = Punjab and District = Amritsar (robust)."""

    # ── STATE ─────────────────────────────
    log_step("Selecting State: Punjab")

    state_input = page.get_by_role("combobox", name=re.compile("State", re.IGNORECASE)).first
    state_input.wait_for(state="visible", timeout=10000)

    state_input.scroll_into_view_if_needed()
    pause(page, 500)

    state_input.click()
    pause(page, 500)

    state_input.fill("Punjab")

    state_option = page.get_by_role(
        "option",
        name=re.compile(r"Punjab", re.IGNORECASE)
    ).first

    state_option.wait_for(state="visible", timeout=10000)
    state_option.click()

    log_step("Selected State: Punjab")

    # 🔥 WAIT for district to reload properly (IMPORTANT)
    page.wait_for_timeout(1000)
    page.wait_for_load_state("networkidle")

    # ── DISTRICT ─────────────────────────
    log_step("Selecting District: Amritsar")

    district_input = page.get_by_role("combobox", name=re.compile("District", re.IGNORECASE)).first
    district_input.wait_for(state="visible", timeout=10000)

    district_input.scroll_into_view_if_needed()
    pause(page, 500)

    district_input.click()
    pause(page, 500)

    district_input.fill("Amritsar")

    district_option = page.get_by_role(
        "option",
        name=re.compile(r"Amritsar", re.IGNORECASE)
    ).first

    district_option.wait_for(state="visible", timeout=10000)
    district_option.click()

    log_step("Selected District: Amritsar")
    pause(page, 2000)


def select_bank_name(page) -> None:
    """Select 'Punjab Gramin Bank' from the Bank Name dropdown."""
    log_step("Selecting bank name: Punjab Gramin Bank")

    bank_name_targets = [
        page.get_by_role("combobox", name="Bank Name"),
        page.locator("label:has-text('Bank Name')").locator(
            "xpath=following::div[contains(@class,'MuiInputBase-root')][1]"
        ),
        page.locator("text=Bank Name").locator(
            "xpath=following::div[contains(@class,'MuiInputBase-root')][1]"
        ),
    ]

    for target in bank_name_targets:
        try:
            if target.count() and target.first.is_visible():
                target.first.scroll_into_view_if_needed()
                pause(page, 500)

                try:
                    target.first.click()
                except Exception:
                    target.first.click(force=True)

                pause(page, 1000)

                option = page.get_by_role(
                    "option",
                    name=re.compile(r"Punjab Gramin Bank", re.IGNORECASE)
                ).first

                option.wait_for(state="visible", timeout=10000)
                option.click()

                log_step("Selected bank name.")
                pause(page, 2000)
                return
        except Exception:
            continue

    raise RuntimeError("Could not open or select the Bank Name dropdown.")

def select_branch(page) -> None:
    """Select 'DHARAR' from the Branch dropdown."""
    branch_name = "DHARAR"
    log_step(f"Selecting branch: {branch_name}")

    # 🔹 Always use real input (combobox)
    branch_input = page.get_by_role(
        "combobox",
        name=re.compile("Branch", re.IGNORECASE)
    ).last

    branch_input.wait_for(state="visible", timeout=10000)
    branch_input.scroll_into_view_if_needed()
    pause(page, 500)

    # 🔹 Click + type (VERY IMPORTANT for MUI)
    branch_input.click()
    pause(page, 500)

    branch_input.fill(branch_name)
    pause(page, 800)

    # 🔹 Correct regex (escaped)
    option = page.get_by_role(
        "option",
        name=re.compile(re.escape(branch_name), re.IGNORECASE)
    ).first

    option.wait_for(state="visible", timeout=10000)

    try:
        option.click()
    except Exception:
        option.click(force=True)

    log_step("Selected branch.")
    pause(page, 2000)

def click_next(page) -> None:
    """Click the Next button."""
    log_step("Clicking Next.")

    next_button = page.get_by_role("button", name="Next").first
    next_button.wait_for(state="visible", timeout=10000)

    pause(page, 1000)
    next_button.click()

    log_step("Clicked Next.")
    pause(page, 2500)

def click_add_land(page) -> None:
    """Click the Add button to add land details."""
    log_step("Clicking Add to add land details.")

    add_button = page.get_by_role("button", name=re.compile(r"Add", re.IGNORECASE)).first
    add_button.wait_for(state="visible", timeout=10000)

    add_button.scroll_into_view_if_needed()
    pause(page, 1000)

    try:
        add_button.click()
    except Exception:
        add_button.click(force=True)

    log_step("Clicked Add.")
    pause(page, 2500)


def select_combobox_option_by_id(page, input_id: str, value: str, label: str) -> None:
    """Select a value from a combobox input using its exact id."""
    field = page.locator(f"#{input_id}")
    field.wait_for(state="visible", timeout=10000)
    field.scroll_into_view_if_needed()
    pause(page, 500)

    try:
        field.click()
    except Exception:
        field.click(force=True)

    pause(page, 500)

    try:
        field.fill("")
        field.fill(value)
    except Exception:
        page.keyboard.press("Meta+A")
        page.keyboard.type(value)

    option = page.get_by_role(
        "option",
        name=re.compile(rf"^{re.escape(value)}$", re.IGNORECASE)
    ).first
    option.wait_for(state="visible", timeout=10000)

    try:
        option.click()
    except Exception:
        option.click(force=True)

    log_step(f"Selected {label}: {value}")
    pause(page, 1500)


def select_district_amritsar(page) -> None:
    """Select District = Amritsar."""
    log_step("Selecting district: Amritsar")
    select_combobox_option_by_id(page, "districtMasterId", "Amritsar", "district")
    pause(page, 1000)


def select_subdistrict_ajnala(page) -> None:
    """Select Sub-District = Ajnala."""
    log_step("Selecting sub-district: Ajnala")
    field = page.locator("#subDistrictMasterId")
    field.wait_for(state="visible", timeout=10000)
    field.scroll_into_view_if_needed()
    pause(page, 1000)
    select_combobox_option_by_id(page, "subDistrictMasterId", "Ajnala", "sub-district")

def select_village_aliwal(page) -> None:
    """Select Village = Aliwal (117)."""
    log_step("Selecting village: Aliwal (117)")

    field = page.locator("#villageId")
    field.wait_for(state="visible", timeout=10000)
    field.scroll_into_view_if_needed()
    pause(page, 1000)

    select_combobox_option_by_id(
        page,
        "villageId",
        "Aliwal (117)",
        "village"
    )

def fill_punjab_land_numbers(page) -> None:
    """Fill Hadbast, Khewat, Khatoni, Khasara numbers."""
    
    numbers = [str(random.choice([1, 2, 3, 12, 32, 123, 321, 1234])) for _ in range(4)]

    log_step(f"Filling Punjab land numbers: {numbers}")

    fields = [
        ("#surveyNo", "Hadbast No", numbers[0]),
        ("#khewatNo", "Khewat No", numbers[1]),
        ("#khatoniNo", "Khatoni No", numbers[2]),
        ("#khasaraNo", "Khasara No", numbers[3]),
    ]

    for selector, label, value in fields:
        field = page.locator(selector)
        field.wait_for(state="visible", timeout=10000)
        field.scroll_into_view_if_needed()
        pause(page, 500)

        field.fill(value)

        log_step(f"{label} filled: {value}")
        pause(page, 500)

    pause(page, 1000)























# def click_add_land_details_for_survey(page, survey_number: str) -> None:
#     """Scroll down and click Add Land Details for the entered survey number."""
#     log_step(f"Adding land details for survey number: {survey_number}")

#     page.mouse.wheel(0, 1200)
#     pause(page, 1000)

#     land_row = page.locator(
#         f"xpath=//*[self::tr or self::div][.//*[contains(normalize-space(), '{survey_number}')]]"
#     ).first

#     land_row.wait_for(state="visible", timeout=10000)
#     land_row.scroll_into_view_if_needed()
#     pause(page, 500)

#     add_buttons = [
#         land_row.locator(
#             "xpath=ancestor::*[contains(@class,'MuiPaper-root') or contains(@class,'MuiCard-root')][1]//button[contains(.,'Add')]"
#         ).first,
#         page.get_by_role("button", name=re.compile(r"Add Land Details", re.IGNORECASE)).first,
#         page.get_by_role("button", name=re.compile(r"Add", re.IGNORECASE)).last,
#     ]

#     for button in add_buttons:
#         try:
#             if button.count() and button.is_visible():
#                 button.scroll_into_view_if_needed()
#                 pause(page, 500)

#                 try:
#                     button.click()
#                 except Exception:
#                     button.click(force=True)

#                 log_step(f"Clicked Add Land Details for survey number {survey_number}.")
#                 pause(page, 2500)
#                 return
#         except Exception:
#             continue

#     raise RuntimeError(f"Could not find Add Land Details button for survey number {survey_number}.")


def fill_input_with_fallback(page, selectors, value: str, label: str, press_enter: bool = False) -> None:
    """Fill a visible text input using multiple fallback locators."""
    last_error = None
    for selector in selectors:
        try:
            field = selector.first
            field.wait_for(state="visible", timeout=5000)
            field.scroll_into_view_if_needed()
            pause(page, 400)

            try:
                field.click()
            except Exception:
                field.click(force=True)

            pause(page, 250)

            try:
                field.fill("")
                pause(page, 150)
                field.fill(value)
            except Exception:
                page.keyboard.press("Meta+A")
                page.keyboard.type(value)

            if press_enter:
                page.keyboard.press("Enter")

            pause(page, 400)
            entered_value = field.input_value().strip()
            if entered_value:
                log_step(f"Filled {label}: {entered_value}")
                return
        except Exception as exc:
            last_error = exc
            continue

    raise RuntimeError(f"Could not fill {label}. Last error: {last_error}")


def select_dropdown_value(page, selectors, value: str, label: str) -> None:
    """Select a dropdown/autocomplete value using multiple fallback locators."""
    last_error = None
    for selector in selectors:
        try:
            field = selector.first
            field.wait_for(state="visible", timeout=5000)
            field.scroll_into_view_if_needed()
            pause(page, 400)

            try:
                field.click()
            except Exception:
                field.click(force=True)

            pause(page, 300)

            try:
                field.fill("")
                field.fill(value)
            except Exception:
                page.keyboard.type(value)

            option = page.get_by_role(
                "option",
                name=re.compile(rf"^{re.escape(value)}$", re.IGNORECASE)
            ).first
            option.wait_for(state="visible", timeout=10000)

            try:
                option.click()
            except Exception:
                option.click(force=True)

            log_step(f"Selected {label}: {value}")
            pause(page, 500)
            return
        except Exception as exc:
            last_error = exc
            continue

    raise RuntimeError(f"Could not select {label}: {value}. Last error: {last_error}")


def click_choice_button(page, value: str, label: str) -> None:
    """Click a visible yes/no style button."""
    targets = [
        page.get_by_role("button", name=re.compile(rf"^{re.escape(value)}$", re.IGNORECASE)),
        page.locator(f"button[title='{value}']"),
        page.locator(f"label:has-text('{value}')"),
    ]

    last_error = None
    for target in targets:
        try:
            button = target.first
            button.wait_for(state="visible", timeout=5000)
            button.scroll_into_view_if_needed()
            pause(page, 300)
            try:
                button.click()
            except Exception:
                button.click(force=True)
            log_step(f"Selected {label}: {value}")
            pause(page, 400)
            return
        except Exception as exc:
            last_error = exc
            continue

    raise RuntimeError(f"Could not select {label}: {value}. Last error: {last_error}")


def add_token_input(page, selectors, value: str, label: str) -> None:
    """Fill a chip/free-solo style input and commit it with Enter."""
    last_error = None

    for selector in selectors:
        try:
            base = selector.first
            base.wait_for(state="visible", timeout=5000)
            base.scroll_into_view_if_needed()
            pause(page, 400)

            # Use the locator itself if it is already the real input.
            input_count = base.locator("input").count()
            input_field = base if input_count == 0 else base.locator("input").first
            input_field.wait_for(state="visible", timeout=5000)

            try:
                input_field.click()
            except Exception:
                input_field.click(force=True)

            pause(page, 300)

            try:
                input_field.fill("")
            except Exception:
                page.keyboard.press("Meta+A")
                page.keyboard.press("BackSpace")
            pause(page, 200)

            try:
                input_field.type(value, delay=80)
            except Exception:
                page.keyboard.type(value, delay=80)
            pause(page, 300)

            page.keyboard.press("Enter")
            pause(page, 800)

            current_value = ""
            try:
                current_value = input_field.input_value().strip()
            except Exception:
                current_value = ""

            container_text = ""
            try:
                container_text = input_field.locator(
                    "xpath=ancestor::*[contains(@class,'MuiFormControl-root') or contains(@class,'MuiAutocomplete-root')][1]"
                ).inner_text().strip()
            except Exception:
                container_text = ""

            chip = page.locator(
                f"xpath=//*[contains(@class,'MuiChip-label') and contains(normalize-space(), '{value}')]"
            )

            if chip.count() > 0 or value.lower() in container_text.lower() or current_value == value:
                log_step(f"Filled {label}: {value}")
                return

        except Exception as exc:
            last_error = exc
            continue

    raise RuntimeError(f"Could not fill {label}. Last error: {last_error}")



def fill_land_details_form(page) -> None:
    """Fill the Punjab land details form and save it."""

    land_size = random.choice(["3", "4", "5", "6", "7"])
    irrigation = random.choice(["Drip", "Canal", "Bore Well", "Electric Motor"])

    log_step("Filling Punjab land details form.")

    # 🔹 Land Area
    fill_input_with_fallback(
        page,
        [
            page.get_by_label(re.compile(r"Land Area Size", re.IGNORECASE)),
            page.locator("xpath=//label[contains(., 'Land Area Size')]/following::input[1]"),
        ],
        land_size,
        "land area size",
    )

    # 🔹 Ownership
    select_dropdown_value(
        page,
        [
            page.get_by_label(re.compile(r"Ownership", re.IGNORECASE)),
            page.locator("xpath=//label[contains(., 'Ownership')]/following::input[1]"),
        ],
        "Owner",
        "ownership",
    )

    # 🔹 Owner Name (simple input now)
    fill_input_with_fallback(
        page,
        [
            page.get_by_label(re.compile(r"Owner Name", re.IGNORECASE)),
            page.locator("xpath=//label[contains(., 'Owner Name')]/following::input[1]"),
        ],
        "pal",
        "owner name",
    )

    # 🔹 Source of Irrigation
    select_dropdown_value(
        page,
        [
            page.get_by_label(re.compile(r"Source Of Irrigation", re.IGNORECASE)),
            page.locator("xpath=//label[contains(., 'Source Of Irrigation')]/following::input[1]"),
        ],
        irrigation,
        "source of irrigation",
    )

    # 🔹 Encumbered → No
    select_dropdown_value(
        page,
        [
            page.locator("#encumbered"),
            page.get_by_label(re.compile(r"Encumbered", re.IGNORECASE)),
        ],
        "No",
        "encumbered",
    )

    # 🔹 Present Market Value
    fill_input_with_fallback(
        page,
        [
            page.get_by_label(re.compile(r"Present Market Value", re.IGNORECASE)),
            page.locator("xpath=//label[contains(., 'Present Market Value')]/following::input[1]"),
        ],
        "3456",
        "present market value",
    )

    # 🔹 Save
    save_button = page.get_by_role("button", name="Save").last
    save_button.wait_for(state="visible", timeout=10000)
    save_button.scroll_into_view_if_needed()
    pause(page, 800)

    try:
        save_button.click()
    except Exception:
        save_button.click(force=True)

    log_step("Punjab land details saved.")
    pause(page, 2500)


def fill_crop_details_form(page, survey_number: str | None = None) -> None:
    """Fill crop details form."""
    log_step("Filling crop details form.")

    cultivation_size = random.choice(["1", "2", "3"])

    crop_name = "Strawberry | Any Season Crop"
    select_dropdown_value(
        page,
        [
            page.locator("#cropId"),
            page.get_by_label(re.compile(r"Crop", re.IGNORECASE)),
            page.locator("xpath=//label[contains(normalize-space(), 'Crop')]/following::input[1]"),
        ],
        crop_name,
        "crop name",
    )

    fill_input_with_fallback(
        page,
        [
            page.locator("#sizeOfCultivation"),
            page.get_by_label(re.compile(r"Size Of Cultivation", re.IGNORECASE)),
            page.locator("xpath=//label[contains(normalize-space(), 'Size Of Cultivation')]/following::input[1]"),
        ],
        cultivation_size,
        "cultivation size",
    )

    log_step(f"Entered cultivation size: {cultivation_size}")
    pause(page, 1000)

def save_crop_details(page) -> None:
    """Click Save button and handle 'Add another crop?' popup."""
    log_step("Saving crop details.")

    save_targets = [
        page.get_by_role("button", name="Save").last,
        page.locator("button[type='submit']").filter(has_text="Save").first,
        page.locator("button:has-text('Save')").last,
    ]

    for btn in save_targets:
        try:
            if btn.count() and btn.first.is_visible():
                btn.first.scroll_into_view_if_needed()
                pause(page, 800)

                try:
                    btn.first.click(timeout=5000)
                except Exception:
                    btn.first.click(force=True)

                log_step("Crop details saved.")
                pause(page, 1500)
                break
        except Exception:
            continue
    else:
        raise RuntimeError("Could not find Save button for crop details.")

    # 🔥 Handle "Add another crop?" popup → click No
    log_step("Handling 'Add another crop?' popup.")

    no_targets = [
        page.locator("button.swal2-cancel", has_text="No").first,
        page.get_by_role("button", name=re.compile(r"^No$", re.IGNORECASE)).last,
        page.locator("button:has-text('No')").last,
    ]

    for btn in no_targets:
        try:
            if btn.count() and btn.first.is_visible():
                btn.first.scroll_into_view_if_needed()
                pause(page, 800)

                try:
                    btn.first.click(timeout=3000)
                except Exception:
                    btn.first.click(force=True)

                log_step("Clicked No on 'Add another crop?' popup.")
                pause(page, 2000)
                return
        except Exception:
            continue

    log_step("'Add another crop?' popup did not appear.")

def handle_land_document_and_next(page) -> None:
    """Select 'No' for land document and click Next."""
    log_step("Handling 'Do you want to add Land Document?' section.")

    # 🔹 Click No for land document
    no_targets = [
        page.locator(
            "xpath=//span[contains(text(),'Do you want to add Land Document')]/following::button[@title='No'][1]"
        ),
        page.locator("button[title='No']").last,
        page.get_by_role("button", name=re.compile(r"^No$", re.IGNORECASE)).last,
    ]

    for btn in no_targets:
        try:
            if btn.count() and btn.first.is_visible():
                btn.first.scroll_into_view_if_needed()
                pause(page, 800)

                try:
                    btn.first.click(timeout=3000)
                except Exception:
                    btn.first.click(force=True)

                log_step("Selected No for Land Document.")
                pause(page, 1500)
                break
        except Exception:
            continue
    else:
        raise RuntimeError("Could not select No for Land Document.")

    # 🔹 Click Next
    log_step("Clicking Next after land document.")

    next_targets = [
        page.get_by_role("button", name="Next").last,
        page.locator("button:has-text('Next')").last,
    ]

    for btn in next_targets:
        try:
            if btn.count() and btn.first.is_visible():
                btn.first.scroll_into_view_if_needed()
                pause(page, 800)

                try:
                    btn.first.click(timeout=5000)
                except Exception:
                    btn.first.click(force=True)

                log_step("Clicked Next.")
                pause(page, 2500)
                return
        except Exception:
            continue

    raise RuntimeError("Could not find Next button after Land Document.")


def handle_loan_request_and_next(page) -> None:
    """Handle loan request question and click Next."""
    log_step("Handling loan request page.")

    # 🔹 Select YES
    yes_targets = [
        page.locator(
            "xpath=//div[contains(text(),'loan amount to stay the same')]/following::button[@title='Yes'][1]"
        ),
        page.locator("button[title='Yes']").first,
        page.get_by_role("button", name=re.compile(r"^Yes$", re.IGNORECASE)).first,
    ]

    for btn in yes_targets:
        try:
            if btn.count() and btn.first.is_visible():
                btn.first.scroll_into_view_if_needed()
                pause(page, 800)

                try:
                    btn.first.click(timeout=3000)
                except Exception:
                    btn.first.click(force=True)

                log_step("Selected Yes for loan amount question.")
                pause(page, 1500)
                break
        except Exception:
            continue
    else:
        raise RuntimeError("Could not select Yes for loan request question.")

    # 🔹 Scroll down
    page.mouse.wheel(0, 1500)
    pause(page, 1000)

    

    # 🔹 Click Next
    log_step("Clicking Next on loan request page.")

    next_targets = [
        page.get_by_role("button", name="Next").last,
        page.locator("button:has-text('Next')").last,
    ]

    for btn in next_targets:
        try:
            if btn.count() and btn.first.is_visible():
                btn.first.scroll_into_view_if_needed()
                pause(page, 800)

                try:
                    btn.first.click(timeout=5000)
                except Exception:
                    btn.first.click(force=True)

                log_step("Clicked Next.")
                pause(page, 2500)
                return
        except Exception:
            continue

    raise RuntimeError("Could not find Next button on loan request page.")

def handle_other_details(page) -> None:
    """Handle Other Details page: Add → Cancel → Save → Submit."""
    log_step("Handling Other Details page.")

    # 🔹 Click Add
    add_btn = page.get_by_role("button", name=re.compile(r"Add", re.IGNORECASE)).first
    add_btn.wait_for(state="visible", timeout=10000)

    add_btn.scroll_into_view_if_needed()
    pause(page, 800)

    try:
        add_btn.click()
    except Exception:
        add_btn.click(force=True)

    log_step("Clicked Add.")
    pause(page, 1500)

    # 🔹 Click Cancel
    cancel_btn = page.get_by_role("button", name=re.compile(r"Cancel", re.IGNORECASE)).first
    cancel_btn.wait_for(state="visible", timeout=10000)

    cancel_btn.scroll_into_view_if_needed()
    pause(page, 800)

    try:
        cancel_btn.click()
    except Exception:
        cancel_btn.click(force=True)

    log_step("Clicked Cancel.")
    pause(page, 1500)

    # 🔹 Click Save
    save_targets = [
        page.get_by_role("button", name="Save").last,
        page.locator("button:has-text('Save')").last,
    ]

    for btn in save_targets:
        try:
            if btn.count() and btn.first.is_visible():
                btn.first.scroll_into_view_if_needed()
                pause(page, 800)

                try:
                    btn.first.click(timeout=5000)
                except Exception:
                    btn.first.click(force=True)

                log_step("Clicked Save.")
                pause(page, 2000)
                break
        except Exception:
            continue
    else:
        raise RuntimeError("Could not click Save.")

    # 🔹 Click Submit
    log_step("Clicking Submit.")

    submit_targets = [
        page.get_by_role("button", name="Submit").last,
        page.locator("button:has-text('Submit')").last,
    ]

    for btn in submit_targets:
        try:
            if btn.count() and btn.first.is_visible():
                btn.first.scroll_into_view_if_needed()
                pause(page, 800)

                try:
                    btn.first.click(timeout=5000)
                except Exception:
                    btn.first.click(force=True)

                log_step("Clicked Submit.")
                pause(page, 3000)
                return
        except Exception:
            continue

    raise RuntimeError("Could not click Submit.")


if __name__ == "__main__":
    main()
