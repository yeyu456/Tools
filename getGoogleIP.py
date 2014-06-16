import urllib2
import re
import multiprocessing
import socket
import time
import os
import sys

class GetIP(object):
    def __init__(self):
        self.url = 'https://github.com/justjavac/Google-IPs'
        self.re_rule = r'>(\d+\.\d+\.\d+\.\d+)<'
        self.save_file = 'googleIP.txt'
        
    def save_ip(self):
        re_item = re.compile(self.re_rule)
        try:
            req_page = urllib2.urlopen(self.url)
        except urllib2.HTTPError, e:
            print 'io error'
        except urllib2.URLError, e:
            print 'url error'
        else:
            with open(self.save_file, 'w') as f:
                for line in req_page:
                    match_ip = re.findall(re_item, line)
                    for i in match_ip:
                        f.writelines(i+'\n')
                        
    def analyse_delay(self):
        with open(self.save_file, 'r') as f:
            for ip in f:
                Connect(ip.strip()).start()
        
class Connect(multiprocessing.Process):
    def __init__(self, ipaddr):
        super(Connect, self).__init__()
        self.ipaddr = ipaddr
        self.port1 = 443
        self.port2 = 80
        self.infofile = 'info.txt'
        self.errorfile = 'error.txt'
        
    def run(self):
        end1 = self.connect(self.port1)
        end2 = self.connect(self.port2)
        
        with open(self.infofile, 'a+') as f:
            if end1!=0:
                f.write('%s:%d connect time %s\n' % (self.ipaddr, 
                                                     self.port1, 
                                                     end1))
            if end2!=0:
                f.write('%s:%d connect time %s\n' % (self.ipaddr, 
                                                     self.port2, 
                                                     end2))              
    
    def connect(self, port):
        if port == 443:
            req_url = 'https://' + self.ipaddr
        else:
            req_url = 'http://' + self.ipaddr
        print req_url
        start = time.time()
        try:
            urllib2.urlopen(req_url, None, 3)
        except urllib2.URLError as e:
            with open(self.errorfile, 'a+') as ef:
                ef.write(''.join([self.ipaddr, ':', str(port), ' URLError\n']))
            return 0
        except socket.timeout as e:
            with open(self.errorfile, 'a+') as ef:
                ef.write(''.join([self.ipaddr, ':', str(port), ' socket timeout\n']))
            return 0
        else:
            return time.time() - start
        
if __name__ == '__main__':
    test = GetIP()
    test.save_ip()
    test.analyse_delay()