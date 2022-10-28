from typing import List
from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.chrome.service import Service as ChromiumService
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.utils import ChromeType

'''
  Not thread safe
'''
class DriverService:
  _instances: List[WebDriver] = []

  factory = lambda **args: webdriver.Chrome(*args, service=ChromiumService(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()))
  default_instance: WebDriver = None

  @classmethod
  def new_instance(cls) -> WebDriver:
    instance = cls.factory()
    cls._instances.append(instance)

    return instance

  @classmethod
  def get_instance(cls) -> WebDriver:
    if cls.default_instance is None:
      cls.default_instance = cls.new_instance()

    return cls.default_instance

  @classmethod
  def shutdown(cls):
    for instance in cls._instances:
      instance.close()