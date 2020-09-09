#!/Users/zackamiton/Code/Pyzant/venv/bin/python

from templates import templates

import requests
import json
import os
import re
import time
import atexit
import math

from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

class Browser(webdriver.Chrome):
    def __init__(self, headless=True, implicit_wait=5):
        self._wait = implicit_wait
        self.options = webdriver.ChromeOptions()
        if headless: self.options.add_argument("headless")

        super(Browser, self).__init__(executable_path="/usr/local/bin/chromedriver", options=self.options)
        self.implicitly_wait(implicit_wait)
        atexit.register(self.quit)

    def get_and_wait(self, url, wait_for=10):
        self.get(url)
        self.finish_loading(wait_for)

    def finish_loading(self, wait_for=10):
        WebDriverWait(self, wait_for).until(lambda d: d.execute_script('return document.readyState') == 'complete')

with open(os.path.join(os.path.dirname(__file__), "credentials", "wyzant.json")) as jf: config = json.load(jf)
def login_selenium(driver, tutor):
    driver.get("https://www.wyzant.com/login")

    #Login
    driver.find_elements_by_name('Username')[-1].send_keys(config[tutor]['username'])
    driver.find_elements_by_name('Password')[-1].send_keys(config[tutor]['password'])
    driver.find_element_by_xpath("//button[@formnovalidate]").click()
    driver.finish_loading()

def get_listings(driver, tutor, max_pages="*"):
    while driver.current_url != "https://www.wyzant.com/tutor/jobs":
        driver.get_and_wait("https://www.wyzant.com/tutor/jobs")

    lpp = 10
    total_pages = min(int(driver.find_element_by_class_name("text-bold").text) // lpp + 1, max_pages if isinstance(max_pages, int) else math.inf)

    clients = []

    for page in range(total_pages):
        for listing in driver.find_elements_by_class_name("academy-card"):
            job_header = listing.find_element_by_class_name("job-details-link")
            job_link, job_category = job_header.get_attribute('href'), job_header.text
            student_name = listing.find_element_by_tag_name('p').text
            is_partnership = "Required" in listing.find_element_by_class_name("text-semibold.text-underscore").text
            desc = listing.find_element_by_class_name('job-description').text

            message = build_template(tutor, student_name, job_category, desc)
            if message and not is_partnership:
                print(job_link, message)
                clients.append([job_link, message])
            else:
                print(f"Listing for {student_name} ({'P' if is_partnership else 'NP'}) in category {job_category} was filtered out; link: {job_link}")

        driver.get(f"https://www.wyzant.com/tutor/jobs?page={page+2}")

    return clients


def build_template(tutor, student, subject, desc):
    template_set = templates[tutor]
    replace_set = {"[TEMPLATE]":subject, "[TUTOR]":tutor, "[STUDENT]":student}
    def replace_generics(s):
        for generic, val in replace_set.items(): s = s.replace(generic, val)
        return s

    if not subject in template_set:
        return None
    else:
        if cs_filter(desc.lower()):
            return None
        if re.search(r"(college app|common\s?app)", desc.lower()) and subject != 'College Counseling':
            subject = 'College Counseling'

        return replace_generics(template_set[subject])



def cs_filter(s):
    filter_set = ["camera", "reinforcement learning", "deep learning", "machine learning", "tensorflow", "gpt", # ml stuff
                  "ml", "kubernetes", "nlp", "computer vision", "object detection", "knn", "ai", # more ml stuff
                  "react", "angular", "mern", "stripe", "bootstrap",  # js stuff
                  "unreal", "unity", "roblox", "minecraft",  # gamedev
                  "aws", "xcode", "ptc creo", "azure", "powerbi", "blender", "hadoop",  "arduino", "mobile", # technologies ic/dw teach
                  "c++", "bash", "powershell", "ruby", "sql", "gdb", "graphql", "php", "vhdl", "scheme", "haskell", "kotlin", "verilog", "assembly", # languages
                  "cloud computing", "network", "systems", "testing", "linear programming", "information technology", # fields idw/can't teach
                  "amazon", "in-person", "algorithm", "time complexity", "quaternions", "recurrence", "interview", "biometrics"  # misc
                  ]

    return re.search(re.escape("SPLITHERE".join(filter_set)).replace("SPLITHERE", "|"), s.lower()) is not None

def send_messages(driver, ls, rate):
    for [url, msg] in ls:
        try:
            driver.get_and_wait(url)

            driver.find_element_by_id("personal_message").send_keys(msg)
            for checkbox in driver.find_elements_by_css_selector("input[type='checkbox']"):
                if checkbox.is_selected(): checkbox.click()

            rate_field = driver.find_element_by_id("hourly_rate")
            
            rate_field.clear()
            rate_field.send_keys(rate)

            driver.find_element_by_name("commit").click()
            driver.finish_loading()
        except:
            print(f"Error with {url}; continuing...")


if __name__ == '__main__':
    for tutor in config:
        browser = Browser(headless=True)
        login_selenium(browser, tutor)
        listings = get_listings(browser, tutor, max_pages=5)
        send_messages(browser, listings, config[tutor]["rate"])

