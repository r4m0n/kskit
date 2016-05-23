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
        6: desired reward value (money class, ex: "$99")
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
        self.reward_id, self.money = self.args[5:7]
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
        except Exception as inst:
            print('[' + ctime() + '] Error: reward ID not found! URL = ' + self.manage_url)
            raise inst
        return radio.find_element_by_xpath('../..')

    def _find_selected_pledge(self):
        try: 
            radios = self.driver.find_elements_by_class_name('radio')
            for radio in radios:
                if radio.is_selected():
                    break;
        except Exception as inst:
            print('[' + ctime() + '] Error: reward ID not found!')
            raise inst
        return float(radio.get_attribute('title').replace(',','').split()[0][1:])

    def verify(self):
        self.driver.get(self.manage_url)
        reward = self._find_reward()
        selected = self._find_selected_pledge()
        if self.money != reward.find_element_by_class_name('money').\
           text[:len(self.money)]:
            print('[' + ctime() + '] Error: money mismatch! Expected: "' + self.money + '" found "' + reward.find_element_by_class_name('money').text[:len(self.money)] + '"')
            raise Exception
        self.minimum = float(reward.find_element_by_class_name('radio').\
                             get_attribute('title').replace(',','').split()[0][1:])
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
        elif 'all-gone' not in reward_class:
            print('\n[' + ctime() + '] Attempting snipe...')
            
            reward.click()
            reward.find_element_by_class_name('pledge__checkout-submit').submit()
            self.driver.find_element_by_class_name('js-confirm-yes').click()
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
