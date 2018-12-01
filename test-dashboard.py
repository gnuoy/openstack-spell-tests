#!/usr/bin/env python3

import argparse
import logging
import subprocess
import sys
import tenacity

from selenium.webdriver.support import ui as selenium_ui
from selenium.webdriver import PhantomJS as WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.common.exceptions import ElementNotVisibleException
from urllib.parse import urlparse

import xvfbwrapper

logger = logging.getLogger('horizon_tests')
logger.setLevel(logging.DEBUG)
consoleHandler = logging.StreamHandler()
logger.addHandler(consoleHandler)

def getDashboardIP():
    cmd = ['/snap/bin/juju', 'status', 'openstack-dashboard', '--format',
           'oneline']
    out = subprocess.check_output(cmd)
    return out.split()[2].decode('UTF8')


class TestDashboard:
    """Login to Horizon and launch an instance using WebUI."""

    XPATH_LAUNCH_FROM_MAIN = "//a[@title='Launch Instance']"
    XPATH_FILTER_BOXES = ("//input[@type='text' and "
                          "@placeholder='Click here for filters.']")
    XPATH_INSTANCE_NAME = ("//input[@type='text' and "
                           "@ng-model='model.newInstanceSpec.name']")
    XPATH_LAUNCH_FROM_WIZARD = ("//button["
                                "@ng-click='viewModel.onClickFinishBtn()']")
    XPATH_NEXT_BUTTON = "//button[@class='btn btn-default next']"
    XPATH_UP_ARROW = "//button[@tabindex='0']"
    ID_INSTANCE_NAME_TXT_BOX = "name"
    MAIN_PAGE_TITLE = "Projects - OpenStack Dashboard"
    SECTIONS_WITH_FILTER_BOXES = [
        'source',
        'flavor',
        'networks',
        'security_groups',
        'key_pair']

    def __init__(self, horizon_ip, username, password, domain, phantomjs_exe,
                 image, flavor, network):
        """Setup tests.

        :param horizon_ip: ip address of horizon.
        :type horizon_ip: str
        :param username: Username to login with
        :type username: str
        :param password: Password to login with
        :type password: str
        :param domain: Domain to login to.
        :type domain: str
        :param phantomjs_exe: Location of phantomjs executable.
        :type phantomjs_exe: str
        :param image: Image to use when creating guest.
        :type image: str
        :param image: Flavor to use when creating guest.
        :type image: str
        :param image: Network to attatch guest to.
        :type image: str
        """
        self.phantomjs_exe = phantomjs_exe
        self.driver = self.get_driver()
        self.wait = WebDriverWait(self.driver, 10)
        self.username = username
        self.password = password
        self.domain = domain
        self.horizon_ip = horizon_ip
        self.image = image
        self.flavor = flavor
        self.network = network

    def waitPageChange(self, old_page):
        """Wait for browser to have navigated away from old_page

        :param old_page: Path portion of url of page moving on from.
        :type old_page: str
        """
        old_path = urlparse(old_page).path
        def _check_current_url(_driver):
            return urlparse(_driver.current_url).path != old_path
        self.wait.until(_check_current_url)

    def getDashboardURL(self):
        """Return url for Horizon."""
        return "http://{}:80/horizon".format(self.horizon_ip)

    def get_driver(self):
        """Get the selenium driver object."""
        driver = WebDriver(executable_path=self.phantomjs_exe)
        # https://github.com/ariya/phantomjs/issues/11637
        driver.set_window_size(1124, 850)
        return driver

    def loginToHorizon(self):
        """Login to Horizon."""
        self.driver.get(self.getDashboardURL())
        self.waitPageChange(self.getDashboardURL())

        username_tb = self.driver.find_element_by_name("username")
        password_tb = self.driver.find_element_by_name("password")
        domain_tb = self.driver.find_element_by_name("domain")
        login_button = self.driver.find_element_by_id("loginBtn")

        username_tb.send_keys(self.username)
        password_tb.send_keys(self.password)
        domain_tb.send_keys(self.domain)
        login_button.click()
        self.waitPageChange("{}/auth/login/".format(self.getDashboardURL()))
        assert self.driver.title == self.MAIN_PAGE_TITLE, (
            "{} != {} login probably failed".format(self.driver.title,
                                                    self.MAIN_PAGE_TITLE))

    def navigateToComputePage(self):
        """Navigate to compute page (must have already logged in)."""
        self.driver.get('{}/project/instances/'.format(self.getDashboardURL()))
        self.waitPageChange(
            "{}/horizon/identity".format(self.getDashboardURL()))

    @tenacity.retry(retry=tenacity.retry_if_exception_type(
                        ElementNotVisibleException),
                    stop=tenacity.stop_after_attempt(2),
                    reraise=True,
                    wait=tenacity.wait_fixed(2),
                    after=tenacity.after_log(logger, logging.DEBUG))
    def click_it(self, button):
        """Click the supplied button and retry if needed.

        Click the button and retry if a ElementNotVisibleException is raised.
        ElementNotVisibleException is usually raised if the page has not
        finished loading.

        :param button: Button to be clicked.
        :type button: selenium.webdriver.remote.webelement.WebElement
        """
        button.click()

    @tenacity.retry(retry=tenacity.retry_if_exception_type(
                        ElementNotVisibleException),
                    stop=tenacity.stop_after_attempt(2),
                    reraise=True,
                    wait=tenacity.wait_fixed(2),
                    after=tenacity.after_log(logger, logging.DEBUG))
    def send_it(self, box, text):
        """Send text to textbox.

        Send text to textbox and retry if a ElementNotVisibleException is
        raised.  ElementNotVisibleException is usually raised if the page has
        not finished loading.

        :param box: Box to inster text into.
        :type box: selenium.webdriver.remote.webelement.WebElement
        :param text: Text to put in box.
        :type text: str
        """
        box.send_keys(text)


    def clickInstanceWizardNext(self):
        """Click the 'next' button in wizard."""
        logger.debug("Click next button")
        next_button = self.driver.find_element_by_xpath(
            self.XPATH_NEXT_BUTTON)
        self.click_it(next_button)

    def getFilterBox(self, section):
        """Return the filter box for the given section.

        :param section: The name of the section to get the filter box for.
        :type section: str
        :returns: Filter Box
        :rtype: selenium.webdriver.remote.webelement.WebElement
        """
        idx = self.SECTIONS_WITH_FILTER_BOXES.index(section)
        filter_boxes = self.driver.find_elements_by_xpath(
            self.XPATH_FILTER_BOXES)
        return filter_boxes[idx]

    def getUpArrow(self, section):
        """Return the Up Arrow button for section.

        Source, Flavor and Network all have lists with filters.
        After a filter is applied there should just be one selection. So,
        the box should be the index for this section.

        For the logic here to work:
            *) Section must be processed in order.
            *) Every section with a filter must have used the filter to leave
               a single element.

        :param section: The name of the section to get the element for.
        :type section: str
        :returns: Up arrow button
        :rtype: selenium.webdriver.remote.webelement.WebElement
        """
        idx = self.SECTIONS_WITH_FILTER_BOXES.index(section)
        up_arrows = self.driver.find_elements_by_xpath(self.XPATH_UP_ARROW)
        return up_arrows[idx]

    def filterAndSelect(self, section, selection):
        """Use filter and selct item.

        Use the filter to limit the avbailable options to a single element and
        then select it.

        :param section: The name of the section to get the element for.
        :type section: str
        :param selection: Item to search for.
        :type selection: str
        """
        logger.debug("Section {}. Filtering on {}".format(section, selection))
        self.send_it(self.getFilterBox(section), selection)

        logger.debug("Section {}. Selecting {}".format(section, selection))
        up_button = self.getUpArrow(section)
        self.click_it(up_button)


    def launchInstance(self, instance_name):
        """Launch instance."""
        # Click Launch Instance from main page
        logger.debug("Click Launch Instance from main page")
        main_launch = self.driver.find_element_by_xpath(
            self.XPATH_LAUNCH_FROM_MAIN)
        main_launch.click()
        
        # Click Instance Name text box
        logger.debug("Click Instance Name text box")
        instance_text_box = self.driver.find_element_by_xpath(
            self.XPATH_INSTANCE_NAME)
        self.click_it(instance_text_box)
        logger.debug("Set instance name to {}".format(instance_name))
        self.send_it(instance_text_box, instance_name)
        self.clickInstanceWizardNext()
        
        # Click up arrow to select image
        self.filterAndSelect('source', self.image)
        self.clickInstanceWizardNext()
    
        # Click up arrow to select flavor
        self.filterAndSelect('flavor', self.flavor)
        self.clickInstanceWizardNext()
    
        # Click select network
        self.filterAndSelect('networks', self.network)
    
        # Click Launch
        logger.debug("Click Launch Instance")
        launch_button = self.driver.find_element_by_xpath(
            self.XPATH_LAUNCH_FROM_WIZARD)
        self.click_it(launch_button)
        

    def run_test(self, vm_name):
        """Run Test.

        Login to Horizon and launch and instance.
        """
        try:
            self.loginToHorizon()
            self.navigateToComputePage()
            self.launchInstance(vm_name)
        except Exception as e:
            self.driver.save_screenshot('/tmp/screenshot.png')
            raise e

def parse_args(args):
    """Parse command line arguments.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--username', help='Name of user to login with',
                        required=True)
    parser.add_argument('-p', '--password', help='Password for user',
                        required=True)
    parser.add_argument('-d', '--domain', help='Domain to login to',
                        required=True)
    parser.add_argument('-j', '--phantomjs-exe', help='Path to phantomjs',
                        required=True)
    parser.add_argument('-v', '--vm-name', help='VM Name',
                        required=True)
    parser.add_argument('-f', '--flavor-name', help='Flavor Name',
                        required=True)
    parser.add_argument('-i', '--image-name', help='Image Name',
                        required=True)
    parser.add_argument('-n', '--network-name', help='Network Name',
                        required=True)
    return parser.parse_args(args)


def main():
    """Run tests."""
    args = parse_args(sys.argv[1:])
    tests = TestDashboard(
        getDashboardIP(),
        args.username,
        args.password,
        args.domain,
        args.phantomjs_exe,
        args.image_name,
        args.flavor_name,
        args.network_name)
    tests.run_test(args.vm_name)

if __name__ == "__main__":
    main()
