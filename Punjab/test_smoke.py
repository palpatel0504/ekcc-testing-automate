import pytest
from run import (
    log_step,
    open_sign_in_page,
    fill_mobile_number,
    click_button,
    fetch_otp_from_toast,
    fill_otp_inputs,
    handle_existing_session_popup,
    handle_logout_other_devices_popup,
    select_pal_rakesh_patel_card,
    open_loan_section,
    remove_incomplete_application_if_present,
    confirm_delete_if_popup_appears,
    select_kcc_crop_loan,
    skip_ekyc_popup_if_present,
    select_pmjjby_yes,
    select_bank_type,
    select_state_and_district,
    select_bank_name,
    select_branch,
    click_next,
    click_add_land,
    select_district_amritsar,
    select_subdistrict_ajnala,
    select_village_aliwal, 
    fill_punjab_land_numbers,
    
    fill_land_details_form,
    fill_crop_details_form, 
    save_crop_details,
    handle_land_document_and_next,
    handle_loan_request_and_next,
    handle_other_details,
    pause,
)

def run_step(missing_items, step_name, func, *args, default=None):
    """Run a step, record the failure, and continue."""
    try:
        return func(*args)
    except Exception as exc:
        message = f"{step_name}: {exc}"
        missing_items.append(message)
        log_step(f"Missing/failed step -> {message}")
        return default


def test_smoke_login_and_remove_loan(page):
    """Smoke test: sign in, handle session, open Loan section, remove any incomplete application."""
    missing_items = []

    # ── 1. Open sign-in page ──────────────────────────────────────────────────
    open_sign_in_page(page)

    # ── 2. Fill mobile number and request OTP ─────────────────────────────────
    fill_mobile_number(page)
    log_step("Filled mobile number.")
    pause(page, 1000)

    click_button(page, "Send OTP")
    log_step("Clicked Send OTP.")

    # ── 3. Read OTP from toast and submit ────────────────────────────────────
    otp = fetch_otp_from_toast(page)
    fill_otp_inputs(page, otp)
    log_step("Filled OTP inputs.")
    pause(page, 1000)

    click_button(page, "Login")
    log_step("Clicked Login.")
    pause(page, 3000)

    # ── 4. Handle 'already logged in' popup if it appears ────────────────────
    handle_existing_session_popup(page)
    handle_logout_other_devices_popup(page)

    # ── 5. Select the correct user card ──────────────────────────────────────
    select_pal_rakesh_patel_card(page)

    # ── 6. Navigate to Loan section ──────────────────────────────────────────
    open_loan_section(page)

    # ── 7. Remove any pending incomplete application ──────────────────────────
    remove_incomplete_application_if_present(page)
    confirm_delete_if_popup_appears(page)

    pause(page, 3000)

    # ── 7. Start New Loan Flow ───────────────────────────────
    click_button(page, "Apply for Loan")
    log_step("Clicked Apply for Loan.")
    pause(page, 3000)

    # ── 8. Select Loan Type ──────────────────────────────────
    select_kcc_crop_loan(page)

    # ── 9. Handle eKYC Popup ─────────────────────────────────
    skip_ekyc_popup_if_present(page)

    select_pmjjby_yes(page)

    select_bank_type(page)

    # select_where_to_apply_branch(page)
    select_state_and_district(page)

    select_bank_name(page)

    select_branch(page)

    click_next(page)

    # ── LAND SECTION ─────────────────────────────────────────
    run_step(missing_items, "click_add_land", click_add_land, page)

    run_step(missing_items, "select_district_amritsar", select_district_amritsar, page)
    run_step(missing_items, "select_subdistrict_ajnala", select_subdistrict_ajnala, page)
    run_step(missing_items, "select_village_aliwal", select_village_aliwal, page)
    run_step(missing_items, "fill_punjab_land_numbers", fill_punjab_land_numbers, page)

    run_step(missing_items, "fill_land_details_form", fill_land_details_form, page)

    run_step(missing_items, "fill_crop_details_form", fill_crop_details_form, page)

    run_step(missing_items, "save_crop_details", save_crop_details, page)

    run_step(missing_items, "handle_land_document_and_next", handle_land_document_and_next, page)
    run_step(missing_items, "handle_loan_request_and_next", handle_loan_request_and_next, page)
    run_step(missing_items, "handle_other_details", handle_other_details, page)

    if missing_items:
        summary = " | ".join(missing_items)
        pytest.fail(f"Punjab flow completed with missing/failed steps: {summary}")

    log_step("Smoke test completed successfully.")
