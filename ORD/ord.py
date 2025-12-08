from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
import time
import re

# ==============================================================
# CONFIG
# ==============================================================
options = Options()
options.add_argument("--start-maximized")
options.add_experimental_option("detach", True)

driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 20)

BASE_BROWSE = "https://open-reaction-database.org/browse"

# Store extracted data
extracted_data = []

# ==============================================================
# HELPERS
# ==============================================================

def wait_for_page_ready(timeout=30):
    """Wait for page to be fully loaded with multiple checks"""
    try:
        # Wait for document ready state
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        
        # Wait for jQuery if it exists
        WebDriverWait(driver, 5).until(
            lambda d: d.execute_script("return typeof jQuery === 'undefined' || jQuery.active === 0")
        )
        
        # Small buffer for any final rendering
        time.sleep(0.5)
    except Exception as e:
        print(f"Page load wait timeout: {e}")

def safe_click(element):
    try:
        element.click()
    except Exception:
        driver.execute_script("arguments[0].click();", element)

def scroll_to_bottom():
    for _ in range(5):
        driver.execute_script("window.scrollBy(0, 600);")
        time.sleep(0.5)

def set_pagination_to_100():
    """Set pagination to 100 on browse page"""
    print("\n>>> Setting pagination to 100...")

    try:
        # Wait for pagination to be present and interactable
        select_element = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.ID, "pagination"))
        )
        
        # Scroll into view
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", select_element)
        time.sleep(0.5)
        
        Select(select_element).select_by_value("100")
        print("✓ Pagination set to 100")

        # Wait for page to reload with new pagination
        time.sleep(1)
        wait_for_dataset_list()
        
    except Exception as e:
        print(f"✗ Pagination dropdown not found: {e}")

def set_dataset_pagination_to_100():
    """Set pagination to 100 in individual dataset view"""
    print(">>> Setting dataset view pagination to 100...")
    
    try:
        # Wait for pagination to be present and interactable
        select_element = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.ID, "pagination"))
        )
        
        # Scroll into view
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", select_element)
        time.sleep(0.5)
        
        Select(select_element).select_by_value("100")
        print("✓ Dataset pagination set to 100")
        
        # Wait for the view to update - check that buttons are present
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located(
                (By.XPATH, "//button[contains(text(),'View Full Details')]")
            )
        )
        
        # Additional wait for all content to load
        time.sleep(1)
        
    except Exception as e:
        print(f"✗ Dataset pagination dropdown not found or no buttons: {e}")

def wait_for_dataset_list():
    """Wait for dataset list to be loaded"""
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located(
            (By.XPATH, "//a[contains(@href, '/dataset/ord_dataset-')]")
        )
    )
    time.sleep(0.5)  # Small buffer for complete rendering

def find_dataset_urls_on_page():
    wait_for_dataset_list()
    links = driver.find_elements(By.XPATH, "//a[contains(@href, '/dataset/ord_dataset-')]")
    urls = []
    for l in links:
        href = l.get_attribute("href")
        if href:
            urls.append(href)
    return list(dict.fromkeys(urls))

# ==============================================================
# MODAL, TABS, & EXTRACTION
# ==============================================================

def click_view_full_buttons_wait():
    """Wait for and return all View Full Details buttons"""
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located(
            (By.XPATH, "//button[contains(text(),'View Full Details')]")
        )
    )
    time.sleep(0.5)  # Buffer for all buttons to render
    return driver.find_elements(By.XPATH, "//button[contains(text(),'View Full Details')]")

def scroll_to_inputs_section(timeout=15):
    xpaths = ["//div[@id='inputs']"]
    end_time = time.time() + timeout
    while time.time() < end_time:
        for xp in xpaths:
            try:
                elem = driver.find_element(By.XPATH, xp)
                driver.execute_script("arguments[0].scrollIntoView({behavior:'smooth'});", elem)
                time.sleep(1)
                return True
            except:
                pass
        driver.execute_script("window.scrollBy(0, 400);")
        time.sleep(0.7)
    return False

def scroll_to_outcomes_section_once(timeout=15):
    xpath = "//div[contains(@class,'title') and normalize-space(text())='Outcomes']"
    end_time = time.time() + timeout

    while time.time() < end_time:
        try:
            elem = driver.find_element(By.XPATH, xpath)
            driver.execute_script("arguments[0].scrollIntoView({behavior:'smooth'});", elem)
            time.sleep(1)
            return True
        except:
            driver.execute_script("window.scrollBy(0, 400);")
            time.sleep(0.7)
    return False

def extract_modal_data(section_name="inputs"):
    try:
        # Wait for modal content to be present
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(@class,'data')]//pre"))
        )
        time.sleep(0.3)
        
        pre_elems = driver.find_elements(By.XPATH, "//div[contains(@class,'data')]//pre")
        
        value = None
        role = None
        full_text = ""

        for pre in pre_elems:
            text = pre.text
            full_text += text + "\n"
            
            match_val = re.search(r'"value":\s*"([^"]+)"', text)
            if match_val:
                value = match_val.group(1)

            match_role = re.search(r"(reaction_role|role):\s*(\w+)", text)
            if match_role:
                role = match_role.group(2)

        # Print extracted data to terminal
        print(f"\n    [{section_name.upper()}] Extracted:")
        print(f"      Value: {value}")
        print(f"      Role: {role}")
        if full_text.strip():
            print(f"      Full Text Preview: {full_text[:200]}...")

        return {"section": section_name, "value": value, "reaction_role": role, "full_text": full_text}

    except Exception as e:
        print(f"    [ERROR] Failed to extract from {section_name}: {e}")
        return {"section": section_name, "value": None, "reaction_role": None, "full_text": None}

def wait_for_modal_and_close(section_name="inputs"):
    data = extract_modal_data(section_name)
    extracted_data.append(data)

    close_xpaths = [
        "//div[contains(@class,'close')]",
        "//div[@class='close']",
    ]
    for xp in close_xpaths:
        try:
            btn = WebDriverWait(driver, 8).until(EC.element_to_be_clickable((By.XPATH, xp)))
            safe_click(btn)
            
            # Wait for modal to actually close
            WebDriverWait(driver, 5).until(
                EC.invisibility_of_element_located((By.XPATH, "//div[contains(@class,'modal')]"))
            )
            time.sleep(0.3)
            return
        except:
            continue

def get_input_tabs():
    return driver.find_elements(By.XPATH, "//div[@id='inputs']//div[contains(@class,'tab')]")

def get_outcome_main_tabs():
    return driver.find_elements(By.XPATH,
        "//div[normalize-space(text())='Outcomes']/following-sibling::div//div[@class='tabs']/div"
    )

def get_outcome_product_tabs():
    return driver.find_elements(By.XPATH,
        "//div[@class='sub-section']//div[@class='tabs']/div"
    )

def find_all_code_buttons_in_inputs():
    return driver.find_elements(By.XPATH,
        "//div[@id='inputs']//div[contains(@class,'raw')]//div[contains(@class,'button')]"
    )

def find_all_code_buttons_in_outcomes():
    return driver.find_elements(By.XPATH,
        "//div[contains(@class,'outcomes-view')]//div[contains(@class,'button')]"
    )

def process_input_tabs():
    tabs = get_input_tabs()
    print(f"    Found {len(tabs)} input tabs")
    
    for i, t in enumerate(tabs, 1):
        print(f"    → Clicking input tab {i}/{len(tabs)}")
        safe_click(t)
        time.sleep(0.5)

        buttons = find_all_code_buttons_in_inputs()
        print(f"      Found {len(buttons)} code buttons in this tab")
        
        for j, btn in enumerate(buttons, 1):
            print(f"      → Opening modal {j}/{len(buttons)}")
            safe_click(btn)
            wait_for_modal_and_close("inputs")

def process_outcomes_section():
    main_tabs = get_outcome_main_tabs()
    print(f"    Found {len(main_tabs)} outcome main tabs")
    
    for m_idx, m in enumerate(main_tabs, 1):
        print(f"    → Clicking outcome main tab {m_idx}/{len(main_tabs)}")
        safe_click(m)
        time.sleep(0.5)

        product_tabs = get_outcome_product_tabs()
        print(f"      Found {len(product_tabs)} product tabs")
        
        for p_idx, p in enumerate(product_tabs, 1):
            print(f"      → Clicking product tab {p_idx}/{len(product_tabs)}")
            safe_click(p)
            time.sleep(0.5)

            buttons = find_all_code_buttons_in_outcomes()
            print(f"        Found {len(buttons)} code buttons")
            
            for b_idx, btn in enumerate(buttons, 1):
                print(f"        → Opening modal {b_idx}/{len(buttons)}")
                safe_click(btn)
                wait_for_modal_and_close("outcomes")

# ==============================================================
# MAIN SCRAPER
# ==============================================================

driver.get(BASE_BROWSE)
wait_for_page_ready()
wait_for_dataset_list()

set_pagination_to_100()

page = 1
detail_views_done = 0
datasets_done = 0

while True:
    print(f"\n============ PAGE {page} ============")

    dataset_urls = find_dataset_urls_on_page()
    print(f"Found {len(dataset_urls)} datasets")

    for ds_url in dataset_urls:
        ds_id = ds_url.split("/")[-1]
        print(f"\n>>> Dataset: {ds_id}")

        driver.get(ds_url)
        wait_for_page_ready()

        # SET PAGINATION TO 100 IN DATASET VIEW
        set_dataset_pagination_to_100()

        try:
            view_buttons = click_view_full_buttons_wait()
            print(f"Found {len(view_buttons)} 'View Full Details' buttons")
        except:
            print("No View Full Details found")
            driver.back()
            wait_for_page_ready()
            wait_for_dataset_list()
            continue

        for idx, vb in enumerate(view_buttons, 1):
            print(f"  Processing button {idx}/{len(view_buttons)}...")
            
            # Navigate back to dataset view to ensure fresh state
            driver.get(ds_url)
            wait_for_page_ready()
            set_dataset_pagination_to_100()
            
            # Re-fetch buttons after page reload
            try:
                current_buttons = click_view_full_buttons_wait()
                if idx <= len(current_buttons):
                    safe_click(current_buttons[idx - 1])
                    time.sleep(1)
                    wait_for_page_ready()
                else:
                    print(f"  Button {idx} not found, skipping...")
                    continue
            except Exception as e:
                print(f"  Error clicking button {idx}: {e}")
                continue

            if scroll_to_inputs_section():
                print("  📥 Processing INPUTS section...")
                process_input_tabs()

            if scroll_to_outcomes_section_once():
                print("  📤 Processing OUTCOMES section...")
                process_outcomes_section()

            detail_views_done += 1

        # Navigate back to main browse page
        driver.get(BASE_BROWSE)
        wait_for_page_ready()
        
        # Re-navigate to correct page number if needed
        if page > 1:
            for _ in range(page - 1):
                try:
                    next_btn = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.LINK_TEXT, "Next"))
                    )
                    safe_click(next_btn)
                    time.sleep(2)
                    wait_for_page_ready()
                except:
                    break
        
        set_pagination_to_100()
        datasets_done += 1

    try:
        next_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Next"))
        )
        safe_click(next_btn)
        time.sleep(1)
        wait_for_page_ready()
        wait_for_dataset_list()
        page += 1
    except:
        print("\n>>> FINISHED — No more pages.")
        break

# ==============================================================
# SUMMARY
# ==============================================================

print("\n============ SUMMARY ============")
print("Datasets processed:", datasets_done)
print("Detail views opened:", detail_views_done)
print("Records extracted:", len(extracted_data))

# Show sample of extracted data
if extracted_data:
    print("\n--- Sample of extracted data (first 5 records) ---")
    for i, record in enumerate(extracted_data[:5], 1):
        print(f"\nRecord {i}:")
        print(f"  Section: {record.get('section')}")
        print(f"  Value: {record.get('value')}")
        print(f"  Role: {record.get('reaction_role')}")
        if record.get('full_text'):
            print(f"  Text preview: {record.get('full_text')[:150]}...")

print("\n=================================")

driver.quit()



