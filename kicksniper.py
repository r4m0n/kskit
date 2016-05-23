#!/usr/bin/env python
''' kicksniper.py: A simple Kickstarter reward sniping script.
    Make sure your original pledge value is equal to or higher than the
    value of the target reward before running this script.
    invoke args:
        1: ks username
        2: ks password
        3: creator ID
        4: project ID
        5: desired reward ID
        6: desired reward desc (leading snippet, quoted)
        7: polling interval (seconds) '''
import sys
from selenium import webdriver
from time import sleep, ctime, time
from datetime import timedelta

__author__ = 'Jason Hsu'
__version__ = '1'

class sniper(object):
    def init(self):
        self.credentials = (('user_session_email', self.args[1]),
                            ('user_session_password', self.args[2]))
        self.manage_url = 'http://www.kickstarter.com/projects/' +\
                          self.args[3] + '/' +\
                          self.args[4] + '/pledge/edit?ref=manage_pledge'
        self.reward_id, self.description = self.args[5:7]
        self.sleeper = int(self.args[7])
        self.driver = webdriver.PhantomJS()
        # self.driver = webdriver.Remote(command_executor =\
        #         'http://127.0.0.1:4444/wd/hub', desired_capabilities =\
        #             webdriver.DesiredCapabilities.HTMLUNITWITHJS)
        # Generally Chrome runs faster than the java standalone client.

    def login(self):
        self.driver.get('https://www.kickstarter.com/login')
        for c in self.credentials:
            form = self.driver.find_element_by_id(c[0])
            form.clear()
            form.send_keys(c[1])
        self.driver.find_element_by_id('login').\
            find_element_by_class_name('submit').click()

    def _find_reward(self):
        try: radio = self.driver.find_element_by_id(\
            'backing_backer_reward_id_' + str(self.reward_id))
        except:
            print('[' + ctime() + '] Error: reward ID not found!')
            raise Exception
        return radio.find_element_by_xpath('..')

    def _find_selected_pledge(self):
        try: 
            radios = self.driver.find_elements_by_class_name('radio')
            for radio in radios:
                if radio.is_selected():
                    break;
        except:
            print('[' + ctime() + '] Error: reward ID not found!')
            raise Exception
        return float(radio.get_attribute('title').replace(',','')[1:])

    def verify(self):
        self.driver.get(self.manage_url)
        reward = self._find_reward()
        selected = self._find_selected_pledge()
        if self.description != reward.find_element_by_class_name('short').\
           text[:len(self.description)]:
            print('[' + ctime() + '] Error: description mismatch!')
            raise Exception
        self.minimum = float(reward.find_element_by_class_name('radio').\
                             get_attribute('title').replace(',','')[1:])
        self.original = float(self.driver.find_element_by_id(\
            'backing_original_pledge').get_attribute('value'))
        print('[' + ctime() + '] Current pledge reward value: $' + str(selected))

        # Multiply by 100 and convert to int to do subtraction
        difference = float(((int(selected * 100) - int(self.minimum * 100)) / 100))
        self.pledge = self.original - difference 

        print('[' + ctime() + '] Difference between pledge levels: $' + str(difference))

        if self.pledge < self.minimum:
            print('[' + ctime() + '] Error: pledge amount < target reward!')
            raise Exception
        print('[' + ctime() + '] Target reward: $' + str(self.minimum))
        print('[' + ctime() + '] Original pledge: $' + str(self.original))
        print('[' + ctime() + '] Will change pledge to: $' + str(self.pledge))

    def _snipe(self):
        reward = self._find_reward()
        reward_class = reward.get_attribute('class')
        if 'selected' in reward_class:
            return False
        elif 'disabled' not in reward_class:
            print('\n[' + ctime() + '] Attempting snipe...')
            if self.pledge != self.original:
                print('[' + ctime() + '] Setting pledge to target reward.')
                amount = self.driver.find_element_by_id('backing_amount')
                amount.clear()
                amount.send_keys(str(self.pledge))

            last = self.driver.find_element_by_class_name('last')
            try: last.click() # workaround for checkout_actions obscuring elem
            except: pass      # by forcing selenium to scroll to bottom first

            reward.click()
            self.driver.find_element_by_class_name('submit').submit()
            self.driver.find_element_by_class_name('confirm-yes').click()
            return True # might not have successfully sniped, so check again
        else:
            sys.stdout.write(self._progbar())
            sys.stdout.flush()
            self.count += 1
            return True

    def _progbar(self):
        pb = ''
        if self.count % 50 == 0:    pb += '\n[' + ctime() + '] '
        if self.count % 9 == 0:     pb += u'\u258c'
        else:                       pb += u'\u2584'
        return pb

    def loop(self):
        self.count, armed = 0, True
        while armed:
            self.driver.get(self.manage_url)
            page = self.driver.find_element_by_tag_name('body').\
                   get_attribute('id')
            if page in ('user_sessions_new',):
                self.login()
            elif page in ('pledges_edit',):
                armed = self._snipe()
                if armed: sleep(self.sleeper)

def main(args):
    if len(args) < 8:
        return 'Error: check arguments!'

    mysniper = sniper()
    mysniper.args = args
    commands = (('Initializing Kicksniper...', mysniper.init),
                ('Logging into Kickstarter...', mysniper.login),
                ('Verifying inputs...', mysniper.verify),
                ('Entering loop...', mysniper.loop))

    print('')
    start_time = time()
    for c in commands:
        print('[' + ctime() + '] ' + c[0])
        c[1]()
    run_time = time() - start_time

    print('[' + ctime() + '] Success! (' + str(mysniper.count) +\
          ' runs, ' + str(timedelta(seconds = int(run_time))) + ' run time)')
    raw_input('Press any key to exit...\n')

if __name__ == '__main__':
    sys.exit(main(sys.argv))
