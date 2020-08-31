import requests
import json
import os
import re
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

with open(os.path.join(os.path.dirname(__file__), "credentials", "wyzant.json")) as jf: creds = json.load(jf)
def login_requests():
    with requests.Session() as session:
        request_token = re.search("(?<=__RequestVerificationToken=)(.*?)(?=;)", session.get("https://www.wyzant.com/login").headers['set-cookie']).group()
        response = session.post("https://www.wyzant.com/sso/login", data=creds, headers={"__RequestVerificationToken":request_token})
        print(session.get('https://www.wyzant.com/tutor/jobs').content)

def make_browser(headless=True):
    options = webdriver.ChromeOptions()
    if headless: options.add_argument("headless")
    browser = webdriver.Chrome(options=options)
    browser.implicitly_wait(10  )
    return browser

def login_selenium():
    browser = make_browser(False)
    browser.get("https://www.wyzant.com/login")

    #Login
    browser.find_elements_by_name('Username')[-1].send_keys(creds['username'])
    browser.find_elements_by_name('Password')[-1].send_keys(creds['password'])
    browser.find_element_by_xpath("//button[@formnovalidate]").click()

    WebDriverWait(browser, 10).until(lambda d: d.execute_script('return document.readyState') == 'complete')

    #Open Jobs Page; seems to get stuck otherwise!
    while browser.current_url != "https://www.wyzant.com/tutor/jobs":
        browser.get("https://www.wyzant.com/tutor/jobs")

    lpp = 10
    for page in range(int(browser.find_element_by_class_name("text-bold").text) // lpp + 1):
        for i, listing in enumerate(browser.find_elements_by_class_name("academy-card")):
            job_header = listing.find_element_by_class_name("job-details-link")
            job_link, job_category = job_header.get_attribute('href'), job_header.text
            student_name = listing.find_element_by_tag_name('p').text
            desc = listing.find_element_by_class_name('job-description').text


            print(student_name, job_category, job_link, desc)

        browser.get(f"https://www.wyzant.com/tutor/jobs?page={page+2}")

if __name__ == '__main__':
    login_selenium()