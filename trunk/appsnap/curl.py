# Import required libraries
import pycurl
import urllib
import _winreg
import string
import socket
import os
import sys

# Don't quote these characters
QUOTE = ':./'

class curl:
    # Constructor
    def __init__(self, global_config):
        # Set up pycurl
        self.global_config = global_config
        self.curl = pycurl.Curl()

        # Get proxy settings from IE if possible
        try:
            key = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, 'Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings')
            proxy_enabled, temp = _winreg.QueryValueEx(key, 'ProxyEnable')
            proxy_info, temp = _winreg.QueryValueEx(key, 'ProxyServer')
            _winreg.CloseKey(key)

            if proxy_enabled == 1:
                # Split server and port
                proxy_server, proxy_port = proxy_info.split(':')

                # Set proxy server and port
                self.curl.setopt(pycurl.PROXY, socket.getfqdn(proxy_server.__str__()))
                self.curl.setopt(pycurl.PROXYPORT, string.atoi(proxy_port))

                self.curl.setopt(pycurl.PROXYUSERPWD, self.global_config.user['proxy_user'] +
                    ':' + self.global_config.user['proxy_password'])
                self.curl.setopt(pycurl.PROXYAUTH, 8)
        except WindowsError: pass

        self.curl.setopt(pycurl.FOLLOWLOCATION, True)
        self.curl.setopt(pycurl.MAXREDIRS, 5)

    # Get the specified URL
    def get_url(self, url, callback):
        # Quote URL as needed
        url = urllib.quote(url, QUOTE)

        # Set the URL and callback function
        self.curl.setopt(pycurl.URL, url)
        self.curl.setopt(pycurl.WRITEFUNCTION, callback)

        # Perform the get
        self.curl.perform()

        # Return the response code
        return self.curl.getinfo(pycurl.RESPONSE_CODE)

    # Download data from the web
    def get_web_data(self, url):
        # Reset output buffer
        self.web_data = ''

        # Download the page
        response = self.get_url(url, self.call_back_buffer)
        if response >= 300:
            if response == 407: print '\nProxy authentication failed. Check config.ini'
            else: print '\nError ' + response.__str__() + ' for URL ' + url

            # Failure occurred so return false
            return None

        # Return the collected data
        return self.web_data

    # Callback function used by pycurl to append data to buffer
    def call_back_buffer(self, buf):
        self.web_data += buf

    # Download data from the web
    def download_web_data(self, url, filename):
        # Create cache directory
        if not os.path.exists(self.global_config.cache['cache_location']):
            os.mkdir(self.global_config.cache['cache_location'])

        # Open download filename
        cached_filename = self.get_cached_name(filename)
        self.download_data = open(cached_filename, 'wb')

        # Download data
        response = self.get_url(url + filename, self.call_back_download)
        if response >= 300:
            # Close and delete download file
            self.download_data.close()
            os.remove(cached_filename)

            # Print the message
            if response == 407: print '\nProxy authentication failed. Check config.ini'
            else: print '\nError ' + response.__str__() + ' while downloading ' + url + filename

            # Failure occurred so return false
            return False

        # Close download file
        self.download_data.close()

        # Success
        return True

    # Callback function used by pycurl
    def call_back_download(self, buf):
        self.download_data.write(buf)

    # Return the filename with the cache dir prepended
    def get_cached_name(self, filename):
        return self.global_config.cache['cache_location'] + '\\' + filename

    def __del__(self):
        self.curl.close()