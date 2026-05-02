import pytest
from run import (
    open_sign_in_page, fill_mobile_number, click_button, fetch_otp_from_toast,
    fill_otp_inputs, handle_existing_session_popup, select_pal_rakesh_patel_card,
    open_loan_section, remove_incomplete_application_if_present,
    confirm_delete_if_popup_appears, select_kcc_crop_loan, skip_ekyc_popup_if_present,
    select_pmjjby_yes, select_bank_type, select_where_to_apply_branch,
    select_bank_name, select_branch, click_next, click_add_land, select_land_location,
    fill_survey_number, click_add_land_details_for_survey, fill_land_details_form,
    select_land_row_by_survey_number, click_add_crop_details,fill_crop_details_form,
    save_crop_details,handle_land_document_and_next,handle_loan_request_and_next,handle_other_details,
    pause, log_step
)

def test_farmer_loan_application_smoke(page, request):
    """End-to-end smoke test for the farmer loan application process."""
    page.set_default_timeout(15000)
    page.set_default_navigation_timeout(30000)
    
    log_step("Starting Pytest E2E Smoke Test")
    
    open_sign_in_page(page)
    pause(page)
    
    log_step("Entering mobile number.")
    fill_mobile_number(page)
    pause(page)
    
    log_step("Clicking Send OTP.")
    click_button(page, "Send OTP")
    pause(page, 1800)
    
    log_step("Fetching OTP from toast.")
    otp = fetch_otp_from_toast(page)
    pause(page, 500)
    
    log_step("Entering OTP.")
    fill_otp_inputs(page, otp)
    pause(page)
    
    log_step("Clicking Login.")
    click_button(page, "Login")
    pause(page, 1800)
    
    log_step("Checking for logout-from-other-devices popup.")
    handle_existing_session_popup(page)
    
    log_step("Selecting Pal Rakesh Patel card.")
    select_pal_rakesh_patel_card(page)
    
    log_step("Opening Loan section.")
    open_loan_section(page)
    
    log_step("Checking for incomplete application.")
    remove_incomplete_application_if_present(page)
    
    log_step("Checking for delete confirmation popup.")
    confirm_delete_if_popup_appears(page)
    
    log_step("Clicking Apply for Loan.")
    click_button(page, "Apply for Loan")
    pause(page, 2500)
    
    log_step("Selecting KCC-Crop loan.")
    select_kcc_crop_loan(page)
    
    log_step("Checking for eKYC popup.")
    skip_ekyc_popup_if_present(page)
    
    log_step("Selecting Yes for PMJJBY/PMSBY/APY.")
    select_pmjjby_yes(page)
    
    log_step("Selecting bank type.")
    select_bank_type(page)
    
    log_step("Selecting 'Where to apply?' as Branch.")
    select_where_to_apply_branch(page)
    
    log_step("Selecting bank name.")
    select_bank_name(page)
    
    log_step("Selecting branch.")
    select_branch(page)
    
    log_step("Clicking Next.")
    click_next(page)
    
    click_add_land(page)
    select_land_location(page)
    survey_number = fill_survey_number(page)
    click_add_land_details_for_survey(page, survey_number)
    fill_land_details_form(page)
    
    select_land_row_by_survey_number(page, survey_number)
    click_add_crop_details(page)
    fill_crop_details_form(page, survey_number)
    save_crop_details(page)
    handle_land_document_and_next(page)
    handle_loan_request_and_next(page)
    handle_other_details(page)
    
    log_step("Smoke Test Completed Successfully")
    
    if request.config.getoption("--headed"):
        log_step("Browser will stay open for you.")
        page.wait_for_timeout(360000000)
