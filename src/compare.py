from selenium import webdriver
from selenium.webdriver.common.by import By

driver = webdriver.Chrome()
driver.get("https://www.astrazeneca.ua/")

# Combined XPath for <img> and <svg> with 'logo' in key attributes
logo_elements = driver.find_elements(By.XPATH,
    "//img[contains(@class, 'logo') or contains(@id, 'logo') or contains(@alt, 'logo') or contains(@src, 'logo')] | " +
    "//svg[contains(@class, 'logo') or contains(@id, 'logo')]"
)

# Process the found elements
print(logo_elements)
for elem in logo_elements:
    img_src = elem.get_attribute('src')
    break
print(img_src)
driver.quit()