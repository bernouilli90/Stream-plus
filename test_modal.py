import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Configurar Chrome
options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

driver = webdriver.Chrome(options=options)
driver.get('http://localhost:5000/auto-assign')

# Esperar a que cargue la página
WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.CSS_SELECTOR, 'button[title="Edit rule"]'))
)

# Hacer clic en el segundo botón de editar (índice 1)
edit_buttons = driver.find_elements(By.CSS_SELECTOR, 'button[title="Edit rule"]')
if len(edit_buttons) > 1:
    edit_buttons[1].click()

    # Esperar a que se abra el modal
    WebDriverWait(driver, 5).until(
        EC.visibility_of_element_located((By.ID, 'ruleModal'))
    )

    # Tomar captura de pantalla
    driver.save_screenshot('modal_after_fix.png')
    print('Screenshot saved as modal_after_fix.png')
else:
    print('Not enough edit buttons found')

driver.quit()