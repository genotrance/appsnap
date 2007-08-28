# Import required libraries
import config
import defines
import os
import pycurl
import socket
import string
import strings
import sys
import threading
import time
import urllib
import _winreg

# Don't quote these characters
QUOTE = ':./?=&'

# Proxy strings
INTERNET_SETTINGS_KEY = 'Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings'
PROXY_ENABLE = 'ProxyEnable'
PROXY_SERVER = 'ProxyServer'

class curl:
    # Constructor
    def __init__(self, global_config):
        # Set up pycurl
        self.global_config = global_config
        self.download = int(self.global_config.network[config.DOWNLOAD])
        
        # Curl object lists
        self.lock = []
        self.acquired = {}
        self.curl = []
        self.web_data = []
        self.download_data = []
        
        for i in range(self.download):
            # Initialize objects
            self.lock.append(threading.Lock())
            self.curl.append(pycurl.Curl())
            self.web_data.append(None)
            self.download_data.append(None)
    
            # Get proxy settings from IE if possible
            try:
                key = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, INTERNET_SETTINGS_KEY)
                proxy_enabled, temp = _winreg.QueryValueEx(key, PROXY_ENABLE)
                proxy_info, temp = _winreg.QueryValueEx(key, PROXY_SERVER)
                _winreg.CloseKey(key)
    
                if proxy_enabled == 1:
                    # Get rid of protocol if specified
                    if proxy_info[:7] == 'http://': proxy_info = proxy_info[7:]
                    if proxy_info[:6] == 'ftp://': proxy_info = proxy_info[6:]
                    
                    try:
                        # Split server and port
                        proxy_server, proxy_port = proxy_info.rsplit(':', 1)
                    except ValueError:
                        # Only server available
                        proxy_server = proxy_info
                        proxy_port = None
    
                    # Set proxy server and port
                    self.curl[i].setopt(pycurl.PROXY, socket.getfqdn(proxy_server.__str__()))
                    if proxy_port != None:
                        self.curl[i].setopt(pycurl.PROXYPORT, string.atoi(proxy_port))
    
                    self.curl[i].setopt(pycurl.PROXYUSERPWD, self.global_config.user[config.PROXY_USER] +
                        ':' + self.global_config.user[config.PROXY_PASSWORD])
                    self.curl[i].setopt(pycurl.PROXYAUTH, defines.CURLOPT_PROXY_ANY)
            except WindowsError: pass
    
            self.curl[i].setopt(pycurl.FOLLOWLOCATION, True)
            self.curl[i].setopt(pycurl.MAXREDIRS, defines.NUM_MAX_REDIRECTIONS)

    # Acquire a lock
    def get_lock(self):
        sleep = 1
        sleep_increment = 1
        while 1:
            for i in range(self.download):
                if self.lock[i].acquire(0) == True:
                    return i
            time.sleep(sleep)
            sleep += sleep_increment
            
    # Release a lock
    def free_lock(self, i):
        self.lock[i].release()

    # Get the specified URL
    def get_url(self, url, i, callback, test=False):
        # Save thread name
        self.acquired[threading.currentThread().getName()] = i

        # Quote URL as needed
        url = urllib.quote(url, QUOTE)

        # Set the URL and callback function
        self.curl[i].setopt(pycurl.URL, url)
        self.curl[i].setopt(pycurl.WRITEFUNCTION, callback)

        # Perform the get
        try: self.curl[i].perform()
        except pycurl.error, message:
            errno, text = message
            # Timeout test then succeeded
            if  errno == defines.ERROR_CURL_OPERATION_TIMEOUT and test == True:
                return 200
            return 404

        # Return the response code
        return self.curl[i].getinfo(pycurl.RESPONSE_CODE)

    # Download data from the web
    def get_web_data(self, url):
        # Get lock
        i = self.get_lock()
        
        # Reset output buffer
        self.web_data[i] = ''

        # Download the page
        response = self.get_url(url, i, self.call_back_buffer)
        if response >= 300:
            if response == 407: print '\n' + strings.PROXY_AUTHENTICATION_FAILED
            else: print '\n' + strings.ERROR + ' '  + response.__str__() + '. URL = ' + url

            # Failure occurred so return false
            self.free_lock(i)
            return None

        # Free lock
        web_data = self.web_data[i]
        self.free_lock(i)

        # Return the collected data
        return web_data

    # Callback function used by pycurl to append data to buffer
    def call_back_buffer(self, buf):
        i = self.acquired[threading.currentThread().getName()]
        self.web_data[i] += buf

    # Download data from the web
    def download_web_data(self, url, filename, referer, progress_callback=None, test=False):
        # Get lock
        i = self.get_lock()
        
        # Create cache directory
        self.global_config.create_cache_directory()

        # If test mode, download to different file and set timeout
        cached_filename = self.get_cached_name(filename)
        if test == True:
            self.curl[i].setopt(pycurl.TIMEOUT, defines.NUM_SECONDS_TO_TEST_DOWNLOAD)
            cached_filename += '.tmp'

        # Open download filename
        self.download_data[i] = open(cached_filename, 'wb')

        # Set progress callback if specified
        if progress_callback != None:
            self.curl[i].setopt(pycurl.NOPROGRESS, 0)
            self.curl[i].setopt(pycurl.PROGRESSFUNCTION, progress_callback)
            
        # Download data
        self.curl[i].setopt(pycurl.REFERER, referer)
        response = self.get_url(url + filename, i, self.call_back_download, True)
        if response >= 300:
            # Close and delete download file
            self.download_data[i].close()
            os.remove(cached_filename)

            # Print the message
            if response == 407: print '\n' + strings.PROXY_AUTHENTICATION_FAILED
            else: print '\n' + strings.ERROR + ' ' + response.__str__() + '. URL = ' + url + filename

            # Failure occurred so return false
            self.free_lock(i)
            return False

        # Close download file
        self.download_data[i].close()
        
        # Free lock
        self.free_lock(i)
        
        # Delete file if test mode
        if test == True: os.remove(cached_filename)

        # Success
        return True

    # Callback function used by pycurl
    def call_back_download(self, buf):
        i = self.acquired[threading.currentThread().getName()]
        self.download_data[i].write(buf)

    # Return the filename with the cache dir prepended
    def get_cached_name(self, filename):
        return os.path.join(self.global_config.cache[config.CACHE_LOCATION], filename)

    # Ensure # of threads per curl object is limited
    def limit_threads(self, threads):
        while len(threads) > defines.NUM_THREADS_PER_CURL_OBJECT * self.download:
            for i in range(len(threads)):
                threads[i].join(defines.NUM_SECONDS_PER_THREAD_JOIN)
                if not threads[i].isAlive():
                    threads.pop(i)
                    break

    # Clear out all threads in queue
    def clear_threads(self, threads):
        while len(threads):
            for i in range(len(threads)):
                threads[i].join(defines.NUM_SECONDS_PER_THREAD_JOIN)
                if not threads[i].isAlive():
                    threads.pop(i)
                    break

    # Destructor
    def __del__(self):
        for i in range(self.download):
            self.curl[i].close()