from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from django.contrib.auth import get_user_model
from decimal import Decimal
import random
import time
import re
import os
import datetime
import traceback

from products.service.product_service import ProductService
from products.unit.action.update_product import UpdateProductAction


class Price:

    def __init__(self):
        self.driver = None
        self.providers = [
            # {
            #     "provider": "Martinez",
            #     "provider_url": "https://shop.mdist.us",
            #     "function": self.get_price_from_martinez
            # },
            {
                "provider": "Sedanos",
                "provider_url": "https://www.sedanos.com",
                "function": self.get_price_from_sedanos
            },
        ]

    def get_price_from_all(self):

        User = get_user_model()
        user = User.objects.filter().first()

        # Lista de User-Agents
        user_agents = [
            # Chrome en Windows 11
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
            # Firefox en Windows 10
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0',
            # Edge en Windows 11
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0'
        ]

        chrome_options = Options()
        # 1. Bloquear imágenes y recursos pesados
        prefs = {
            "profile.default_content_setting_values.images": 2,
            "profile.default_content_settings.popups": 2,  # Bloquear popups
            "profile.default_content_setting_values.notifications": 2,  # No notificaciones
        }
        chrome_options.add_experimental_option("prefs", prefs)
        chrome_options.add_argument(f'user-agent={random.choice(user_agents)}')
        chrome_options.add_argument("--headless=new")  # Modo sin interfaz para servidores
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-extensions")  # Sin extensiones
        chrome_options.add_argument("--disable-notifications")  # Sin notificaciones
        chrome_options.add_argument('--window-size=1920,1080')
        driver = webdriver.Chrome(options=chrome_options)
        self.driver = driver

        try:
            driver.set_page_load_timeout(300)
            # driver.set_page_load_timeout(30)  # 30 segundos para cargar página
            driver.set_script_timeout(20)  # 20 segundos para scripts JS
            driver.implicitly_wait(0)  # Desactivar implícitas (usar solo explícitas)

            wait = WebDriverWait(driver,
                                 timeout=25,  # 25 segundos máximo de espera
                                 poll_frequency=1)  # Verificar cada 1 segundo

            service = ProductService()
            for provider in self.providers:
                set_first_data = True

                products = service.find_all().filter(store_provider_url__startswith=provider.get('provider_url'))
                for product in products:
                    if product.active:
                        print('Inicio ', product.sku)
                        get_price_from = provider.get('function')
                        price, out_of_stock = get_price_from(product.store_provider_url, wait, set_first_data)
                        set_first_data = False
                        print(price)
                        update_product = UpdateProductAction()
                        update_product.set(user, product.pk, product.sku, product.store_provider_url, price, not out_of_stock, None)
                        update_product.execute()
                        print('Termino ', product.sku)
                        time.sleep(random.uniform(3, 6))

        except Exception as e:
            #timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            #os.makedirs("debug", exist_ok=True)
            #driver.save_screenshot(f"debug/debug_{timestamp}.png")
            print(f"Ocurrió un error: {e}")
            traceback.print_exc()
        finally:
            # input()
            driver.quit()

    def get_price_from_sedanos(self, url, wait, set_store):
        self.driver.get(url)

        if set_store:
            wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.fp-btn-select-store'))
            )
            element_select_store_click = self.driver.find_element(By.CSS_SELECTOR, '.fp-btn-select-store')
            print(element_select_store_click.get_attribute("innerText"))
            ActionChains(self.driver).scroll_to_element(element_select_store_click).perform()
            wait.until(
                EC.element_to_be_clickable(element_select_store_click)
            )
            element_select_store_click.click()

            wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.fp-btn-price.fp-btn-mystore[data-store-id="5735"]'))
            )
            element_select_store = self.driver.find_element(By.CSS_SELECTOR, '.fp-btn-price.fp-btn-mystore[data-store-id="5735"]')
            if element_select_store.is_displayed():
                wait.until(
                    EC.presence_of_element_located((By.ID, 'cn-accept-cookie'))
                )
                element_cookie_click = self.driver.find_element(By.ID, 'cn-accept-cookie')
                wait.until(
                    EC.element_to_be_clickable(element_cookie_click)
                )
                element_cookie_click.click()

                ActionChains(self.driver).scroll_to_element(element_select_store).perform()
                wait.until(
                    EC.element_to_be_clickable(element_select_store)
                )
                print(element_select_store.get_attribute("innerText"))
                element_select_store.click()

        script_js = """
            // Versión JavaScript puro de tu jQuery
            var heading = document.querySelector('.container-fluid.fp-page-header');
            if (heading) {
                var priceSpanSale = heading.querySelector('.fp-item-sale strong');
                if (priceSpanSale) {
                    return priceSpanSale.textContent.trim();
                }
                var priceSpan = heading.querySelector('.fp-item-price');
                if (priceSpan) {
                    var priceSpanInner = priceSpan.querySelector('.fp-item-base-price');
                    if (priceSpanInner) {
                        return priceSpanInner.textContent.trim();
                    }
                }
            }
            return null;
            """
        wait.until(lambda d: d.execute_script(script_js) is not None)
        price_text = self.driver.execute_script(script_js)
        price = self.extract_price_from_text(price_text)

        wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, 'fp-item-quantity-on-hand'))
        )
        element_in_stock = self.driver.find_element(By.CLASS_NAME, 'fp-item-quantity-on-hand')
        in_stock = element_in_stock.get_attribute("innerText").strip().upper() == 'In Stock'.upper()
        out_of_stock = not in_stock

        return price, out_of_stock

    def get_price_from_martinez(self, url, wait, set_location):
        price = None
        out_of_stock = False

        self.driver.get(url)

        if set_location:
            wait.until(
                EC.presence_of_element_located((By.ID, "location-dialog"))
            )
            location_dialog = self.driver.find_element(By.ID, "location-dialog")
            if location_dialog:
                wait.until(
                    EC.presence_of_element_located((By.CLASS_NAME, "locations-popup-location-name"))
                )
                list_names = location_dialog.find_elements(By.CLASS_NAME, "locations-popup-location-name")
                for elm in list_names:
                    if elm.get_attribute("innerText").upper().find("Miami".upper()) >= 0:
                        elm_click = elm.find_element(By.XPATH, "./following-sibling::a")
                        elm_click.click()
                        break

        script_js = """
            // Versión JavaScript puro de tu jQuery
            var heading = document.querySelector('.product-heading');
            if (heading) {
                var priceSpan = heading.querySelector('.price span');
                if (priceSpan) {
                    return priceSpan.textContent.trim();
                }
                var outOfStock = heading.querySelector('.out-of-stock');
                if (outOfStock) {
                    return 'out_of_stock';
                }
            }
            return null;
            """

        wait.until(lambda d: d.execute_script(script_js) is not None)
        price_text = self.driver.execute_script(script_js)
        if price_text == 'out_of_stock':
            out_of_stock = True
        else:
            price = self.extract_price_from_text(price_text)

        return price, out_of_stock

    @classmethod
    def extract_price_from_text(cls, text):
        # Patrón que busca números con decimales, opcionalmente precedidos por $ o símbolos
        pattern = r'[\$£€]?\s*(\d+\.?\d*)\s*(?:dollars?|USD|pounds?|EUR)?'
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            return Decimal(match.group(1))
        return None

