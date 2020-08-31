from templates import templates

import requests
import json
import os
import re
import time
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

        super(Browser, self).__init__(options=self.options)
        self.implicitly_wait(implicit_wait)

    @property
    def wait(self): return self._wait

    @wait.setter
    def wait(self, value):
        self._wait = value
        self.implicitly_wait(value)

    def get_and_wait(self, url, wait_for=10):
        self.get(url)
        self.finish_loading(wait_for)

    def finish_loading(self, wait_for=10):
        WebDriverWait(self, wait_for).until(lambda d: d.execute_script('return document.readyState') == 'complete')

with open(os.path.join(os.path.dirname(__file__), "credentials", "wyzant.json")) as jf: creds = json.load(jf)
def login_selenium(driver, tutor):
    driver.get("https://www.wyzant.com/login")

    #Login
    driver.find_elements_by_name('Username')[-1].send_keys(creds[tutor]['username'])
    driver.find_elements_by_name('Password')[-1].send_keys(creds[tutor]['password'])
    driver.find_element_by_xpath("//button[@formnovalidate]").click()
    driver.finish_loading()


def get_listings(driver, tutor, max_pages="*"):
    while driver.current_url != "https://www.wyzant.com/tutor/jobs":
        driver.get_and_wait("https://www.wyzant.com/tutor/jobs")

    lpp = 10
    total_pages = min(int(driver.find_element_by_class_name("text-bold").text) // lpp + 1, max_pages if isinstance(max_pages, int) else math.inf)

    for page in range(total_pages):
        for i, listing in enumerate(driver.find_elements_by_class_name("academy-card")):
            job_header = listing.find_element_by_class_name("job-details-link")
            job_link, job_category = job_header.get_attribute('href'), job_header.text
            student_name = listing.find_element_by_tag_name('p').text
            desc = listing.find_element_by_class_name('job-description').text

            if message := build_template(tutor, student_name, job_category, desc):
                print(f"Reply to {student_name}, {job_category}:")
                print(message)
            else:
                print(f"Listing for {student_name} in category {job_category} was filtered out; link: {job_link}")
        driver.get(f"https://www.wyzant.com/tutor/jobs?page={page+2}")


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
        if re.search("(college app|common\s?app)", desc.lower()) and subject != 'College Counselling':
            subject = 'College Counselling'

        return replace_generics(template_set[subject])


def cs_filter(s):
    filter_set = ["reinforcement learning", "deep learning", "machine learning", "tensorflow", " ml ", "kubernetes", "nlp", "computer vision", #ML filters
                  "react", "angular", #js frameworks
                  "unreal", "unity", "roblox", "minecraft", #gamedev
                  "c++", "bash", "ruby", "sql", "gdb", "graphql", "php" #technologies I can't teach
                  ]

    return any(fs in s for fs in filter_set)


if __name__ == '__main__':
    browser = Browser(headless=False)
    login_selenium(browser, "Zack")
    get_listings(browser, "Zack", max_pages=5)
