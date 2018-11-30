#!/usr/bin/env python3

import argparse
import logging
import subprocess
import sys
import tenacity

from selenium.webdriver.support import ui as selenium_ui
from selenium.webdriver import PhantomJS as WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import ElementNotVisibleException
from urllib.parse import urlparse

import xvfbwrapper

logger = logging.getLogger('horizon_tests')
logger.setLevel(logging.DEBUG)
consoleHandler = logging.StreamHandler()
logger.addHandler(consoleHandler)

def getDashboardIP():
    cmd = ['/snap/bin/juju', 'status', 'openstack-dashboard', '--format', 'oneline']
    out = subprocess.check_output(cmd)
    return out.split()[2].decode('UTF8')


class TestDashboard:

    CSS_IMAGE_UP_ARROW = ".ng-scope:nth-child(1) > .actions_column:nth-child(7) .btn:nth-child(1)" 
    CSS_NETWORK_UP_ARROW = "td.actions_column > action-list.ng-isolate-scope.btn-group > button.btn.btn-default"
    CSS_NEXT_BUTTON = ".next"
    CSS_FLAVOR_UP_ARROW = ".btn-sm"
    CSS_LAUNCH_INSTANCE_BUTTON = ".finish"
    CSS_LAUNCH_INSTANCE_WIZARD_BUTTON = "instances__action_launch-ng"
    ID_INSTANCE_NAME_TXT_BOX = "name"
    MAIN_PAGE_TITLE = "Projects - OpenStack Dashboard"

    def __init__(self, horizon_ip, username, password, domain, phantomjs_exe):
        self.phantomjs_exe = phantomjs_exe
        self.driver = self.get_driver()
        self.wait = WebDriverWait(self.driver, 10)
        self.username = username
        self.password = password
        self.domain = domain
        self.horizon_ip = horizon_ip

    def waitPageChange(self, old_page):
        old_path = urlparse(old_page).path
        def _check_current_url(_driver):
            return urlparse(_driver.current_url).path != old_path
        self.wait.until(_check_current_url)

    def getDashboardURL(self):
        return "http://{}:80/horizon".format(self.horizon_ip)

    def get_driver(self):
        driver = WebDriver(executable_path=self.phantomjs_exe)
        # https://github.com/ariya/phantomjs/issues/11637
        driver.set_window_size(1124, 850)
        return driver

    def loginToHorizon(self):
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
        button.click()

    def clickInstanceWizardNext(self):
        # Click next button
        logger.debug("Click next button")
        next_button = self.driver.find_element_by_css_selector(
            self.CSS_NEXT_BUTTON)
        self.click_it(next_button)

    def launchInstance(self, instance_name):
        # Click Launch Instance from main page
        logger.debug("Click Launch Instance from main page")
        self.driver.find_element_by_id(
            self.CSS_LAUNCH_INSTANCE_WIZARD_BUTTON).click()
        
        # Click Instance Name text box
        logger.debug("Click Instance Name text box")
        instance_text_box = self.driver.find_element_by_id(
            self.ID_INSTANCE_NAME_TXT_BOX)
        self.click_it(instance_text_box)
        logger.debug("Set instance name to {}".format(instance_name))
        instance_text_box.send_keys(instance_name)
        
        self.clickInstanceWizardNext()
        
        # Click up arrow to select image
        logger.debug("Click up arrow to select image")
        image_button = self.driver.find_element_by_css_selector(
            self.CSS_IMAGE_UP_ARROW)
        self.click_it(image_button)

        self.clickInstanceWizardNext()
    
        # Click up arrow to select flavor
        logger.debug("Click up arrow to select flavor")
        flavor_button = self.driver.find_element_by_css_selector(
            self.CSS_FLAVOR_UP_ARROW)
        self.click_it(flavor_button)

        self.clickInstanceWizardNext()
    
        # Click select network
        logger.debug("Click up arrow to select network")
        network_arrow = self.driver.find_element_by_css_selector(
            self.CSS_NETWORK_UP_ARROW)
        self.click_it(network_arrow)
    
        # Click Launch
        logger.debug("Click Launch Instance")
        launch_button = self.driver.find_element_by_css_selector(
            self.CSS_LAUNCH_INSTANCE_BUTTON)
        self.click_it(launch_button)
        

    def run_test(self, vm_name):
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
    parser.add_argument('-p', '--password', help='Passowrd for user',
                        required=True)
    parser.add_argument('-d', '--domain', help='Domain to login to',
                        required=True)
    parser.add_argument('-j', '--phantomjs-exe', help='Path to phantomjs',
                        required=True)
    parser.add_argument('-v', '--vm-name', help='VM Name',
                        required=True)
    return parser.parse_args(args)


def main():
    """Cleanup after test run."""
    args = parse_args(sys.argv[1:])
    tests = TestDashboard(
        getDashboardIP(),
        args.username,
        args.password,
        args.domain,
        args.phantomjs_exe)
    tests.run_test(args.vm_name)

if __name__ == "__main__":
    main()
