import keyboard
import os
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

class Profile:

    def __init__(self):
        self.username = None
        self.password = None
        self.ff_path = None
        self.gecko_path = None
        self.addon_path = None
        self.keys = {"Exit": "alt+escape", "Previous":"alt+left", "Next":"alt+right", "Play/Pause":"alt+space", "Volume Up":"alt+up", "Volume Down":"alt+down"}

    def read_settings(self):
        '''
        Read settings from "SpotKeys_Settings.txt" and return <Profile> object.  Assumes settings file has keyword
        followed by " = " and then desired value.
        '''
        if not os.path.isfile("SpotKeys_Settings.txt"):
            print("Settings file does not exist!")
        else:
            with open("SpotKeys_Settings.txt") as f:
                content = f.readlines()
            for line in content:
                if line.startswith("SPOTIFY_USERNAME"):
                    self.username = line.split("=")[1].strip()
                elif line.startswith("SPOTIFY_PASSWORD"):
                    self.password = line.split("=")[1].strip()
                elif line.startswith("FF_PATH"):
                    self.ff_path = line.split("=")[1].strip()
                elif line.startswith("ADDON_PATH"):
                    self.addon_path = line.split("=")[1].strip()
                else:
                    print("Unexpected setting: ", line)

    def output_key_bindings(self):
        '''
        Output key bindings from <keys> dictionary.
        '''
        print("Key Bindings")
        for k,v in self.keys.items():
            print(f"\t{k}: {v}")

class Hotkey_Tracker:

    def __init__(self):
        self.value = None

    def fire(self, new_value):
        '''
        Set <value> to <new_value>, unhooking hotkeys if this is "Exit".
        '''
        self.value = new_value
        if self.value == "Exit":
            keyboard.unhook_all()

    def clear(self):
        '''
        Reset <value> to <None> so long as it isn't "Exit"
        '''
        if self.value != "Exit":
            self.value = None

class SpotKeys_Manager:

    def __init__(self):
        print("Starting SpotKeys...\n")

        self.settings = Profile()
        self.settings.read_settings()

        self.settings.output_key_bindings()

        # Set hotkeys
        self.tracker = Hotkey_Tracker()
        keyboard.add_hotkey(self.settings.keys["Exit"], self.tracker.fire, args=["Exit"], suppress=True)
        keyboard.add_hotkey(self.settings.keys["Previous"], self.tracker.fire, args=["Previous"], suppress=True)
        keyboard.add_hotkey(self.settings.keys["Next"], self.tracker.fire, args=["Next"], suppress=True)
        keyboard.add_hotkey(self.settings.keys["Play/Pause"], self.tracker.fire, args=["Play/Pause"], suppress=True)
        keyboard.add_hotkey(self.settings.keys["Volume Up"], self.tracker.fire, args=["Volume Up"], suppress=True)
        keyboard.add_hotkey(self.settings.keys["Volume Down"], self.tracker.fire, args=["Volume Down"], suppress=True)

        # Switch to non-root user (required by Firefox)
        original_uid = int(os.getenv("SUDO_UID"))
        os.setreuid(original_uid,original_uid)

        ff_options = Options()
        ff_options.binary_location = self.settings.ff_path
        # Needed to play DRM content
        ff_options.set_preference('media.gmp-manager.updateEnabled',True)
        ff_options.set_preference('media.eme.enabled',True)

        self.driver = webdriver.Firefox(options = ff_options)
        self.driver.get('https://accounts.spotify.com/en/login?continue=https:%2F%2Fopen.spotify.com%2F')
        self.spotkeys_window_handle = self.driver.current_window_handle

        # Apply optional settings parameters if present
        if self.settings.addon_path != None:
            self.driver.install_addon(self.settings.addon_path,temporary=True)
        if self.settings.username != None:
            user_element = self.driver.find_element_by_id('login-username')
            user_element.clear()
            user_element.send_keys(self.settings.username)
            if self.settings.password != None:
                password_element = self.driver.find_element_by_id('login-password')
                password_element.clear()
                password_element.send_keys(self.settings.password)
                password_element.send_keys(Keys.RETURN)

    def close_popups(self):
        try:
            # Cookies Popup
            self.driver.find_element_by_id('onetrust-close-btn-container').click()
        except:
            pass

    def run (self):
        '''
        Listen for hotkeys and execute corresponding actions.
        '''
        last_url = ''
        initialized = False
        while self.tracker.value != "Exit":
            if self.driver.current_window_handle != self.spotkeys_window_handle:
                driver.switch_to_window(self.spotkeys_window_handle)
            if last_url != self.driver.current_url:
                last_url = self.driver.current_url
                btns = self.driver.find_elements_by_xpath('''//div[@class='player-controls__buttons']//button''')
                volume_slider = self.driver.find_elements_by_css_selector('button.middle-align.progress-bar__slider')
                if len(btns) > 3 and len(volume_slider) > 1:
                    volume_slider = volume_slider[1] # Currently 4 such Elements; want the 2nd
                    volume_up = ActionChains(self.driver)
                    volume_up.drag_and_drop_by_offset(volume_slider,10,0)
                    volume_down = ActionChains(self.driver)
                    volume_down.drag_and_drop_by_offset(volume_slider,-10,0)
                    initialized = True
                else:
                    initialized = False
                self.close_popups()
            if initialized:
                if self.tracker.value == "Previous":
                    btns[1].click()
                elif self.tracker.value == "Next":
                    btns[3].click()
                elif self.tracker.value == "Play/Pause":
                    btns[2].click()
                elif self.tracker.value == "Volume Up":
                    volume_up.perform()
                elif self.tracker.value == "Volume Down":
                    volume_down.perform()
                self.tracker.clear()
        self.driver.quit()
        print("\nExiting SpotKeys...\n")

    def get_driver(self):
        return self.driver

if __name__ == "__main__":
    spotkeys = SpotKeys_Manager()
    spotkeys.run()
