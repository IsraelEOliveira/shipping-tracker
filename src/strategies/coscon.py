from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
import selenium.webdriver.support.expected_conditions as ec
from driver import DriverService
from util import chunk
from .tracker import TrackerStrategy


TOKEN = {
  'uri'              : 'https://elines.coscoshipping.com/ebusiness/cargoTracking',
  'trackType'        : (By.CSS_SELECTOR, '.cargoTrackType'),
  'billOpt'          : (By.XPATH, '//ul[@class="ivu-select-dropdown-list"]/div/li[1]'),
  'unitInput'        : (By.CSS_SELECTOR, '#wrap > input'),
  'billTab'          : (By.XPATH, '//div[@class="ivu-tabs-nav-wrap"]//div[contains(text(), "Bill of Lading Information")]'),
  'detailPart'       : (By.CLASS_NAME, 'ivu-c-detailPart'),
  'detailRows'       : (By.CSS_SELECTOR, '.ivu-c-detailLine p'),
  'scriptLabel'      : 'return arguments[0].childNodes[0].textContent',
  'containerTab'     : (By.XPATH, '//div[@class="ivu-tabs-nav-wrap"]//div[contains(text(), "Container Information")]'),
  'container'        : (By.CSS_SELECTOR, '.cntrsList tbody > tr:first-child > td:first-child'),
  'containerTrigger' : (By.CSS_SELECTOR, '.ivu-poptip-rel'),
  'containerPopper'  : (By.CSS_SELECTOR, '.ivu-poptip-popper .ivu-table-body')
}

class CosconTracker(TrackerStrategy):
  driver: WebDriver

  def __init__(self, driver: WebDriver = DriverService.new_instance()):
    self.driver = driver

  def lookup(self, _: str, unit: str) -> dict:
    self._get_bill_page_for_unit(unit)
    return self._scrape()

  def _get_bill_page_for_unit(self, unit: str) -> WebDriver:
    self.driver.get(TOKEN['uri'])

    dom_select = self.driver.find_element(*TOKEN['trackType'])
    dom_select.click()

    '''
      @TODO
      The following line could be
        (By.XPATH, '//li[contains(text(), "Bill Of Lading")]')
      but it throws an error later that prevents the interaction with the input (dom_unit).
      it appears to be a better solution than depending on the combobox order
    '''
    dom_select.find_element(*TOKEN['billOpt']).click()

    dom_unit = self.driver.find_element(*TOKEN['unitInput'])
    dom_unit.click()
    dom_unit.clear()
    dom_unit.send_keys(*unit, Keys.ENTER)

    return self.driver

  def _scrape(self) -> dict:
    detail_part = self._parse_detail_part()
    container = self._parse_container_part()

    return detail_part | container

  def _parse_detail_part(self) -> dict:
    # Ensure bill of lading tab
    dom_bill_tab = WebDriverWait(self.driver, 10).until(
        ec.visibility_of_element_located(TOKEN['billTab']))
    dom_bill_tab.click()

    # Extract main content
    dom_detail_part = self.driver.find_element(*TOKEN['detailPart'])
    dom_rows = dom_detail_part.find_elements(*TOKEN['detailRows'])

    # Scrape pairs of data
    scraped = dict(
        map(lambda pair:
            (
                str(self.driver.execute_script(TOKEN['scriptLabel'], pair[0])).strip(),
                pair[1].text.strip()
            ),
            chunk(dom_rows, 2)
        )
    )

    return scraped

  def _parse_container_part(self) -> dict:
    # Ensure container information tab
    dom_container_tab = WebDriverWait(self.driver, 10).until(
        ec.visibility_of_element_located(TOKEN['containerTab']))
    dom_container_tab.click()

    # Query first container cell
    dom_container = self.driver.find_element(*TOKEN['container'])
    scraped_container = dom_container.find_element(By.CSS_SELECTOR, 'p:first-child').text

    # Trigger popper
    dom_container.find_element(*TOKEN['containerTrigger']).click()
    dom_container_form = WebDriverWait(self.driver, 10).until(
        ec.visibility_of_element_located(TOKEN['containerPopper']))

    # Extract table skipping number column
    dom_rows = dom_container_form.find_elements(By.CSS_SELECTOR, 'tr > td:not(:first-child)')

    # Scrape both columns
    scraped_shipment = list(
        map(lambda pair:
            dict(zip(
              ['what', 'when', 'transport', 'location'],
              [
                *list(map(lambda el:
                  el.text,
                  pair[0].find_elements(By.CSS_SELECTOR, 'p > span:last-child')
                )),
                pair[1].find_element(By.CSS_SELECTOR, 'span').text
              ]
            )),
            chunk(dom_rows, 2)
        )
    )

    scraped = {
      'Container': scraped_container,
      'Shipment cycle': scraped_shipment
    }

    return scraped