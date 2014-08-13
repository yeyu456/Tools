# -*- coding: utf-8 -*-
#!/usr/bin/env python3.4
import http.client
import time
import dns.query, dns.message, dns.exception, dns.rrset, dns.name
import re
import multiprocessing
import configparser
import os.path
import concurrent.futures
import socket
import binascii

#default global setting
headers = {'Host' : 'your default host name',
           'Connection' : 'keep-alive',
           'User-Agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.125 Safari/537.36',
           'Accept-Encoding' : 'gzip,deflate,sdch',
           'Accept-Language' : 'zh-CN,zh;q=0.8,en;q=0.6,ja;q=0.4,ko;q=0.2,zh-TW;q=0.2'}
url = 'filepath in cdn node'
domain = 'your domain name'
debug = False

class CDNTEST(object):
    def __init__(self, dnsFile, dns_timeout, nodeFile, connect_timeout):
        """
        :param dnsFile: file that stores all isp dns server ip address
        :type dnsFile: string or file object same as open()
        :param dns_timeout: dns resolve timeout value with unit of second
        :type dns_timeout: int
        :param nodeFile: file that stores cdn nodes' ip addresses
        :type nodeFile: string or file object same as open()
        :param connect_timeout:http connect timeout value with unit of second
        :type connect_timeout: int
        """
        self.dnsFile = dnsFile
        self.dns_timeout = dns_timeout
        self.nodeFile = nodeFile
        self.connect_timeout = connect_timeout
        self.thread_count = 2
        if self.thread_count < multiprocessing.cpu_count():
            self.thread_count = multiprocessing.cpu_count()

    def host_connect(self):
        """Connect all nodes and resolved nodes to get the connecting time and print the least one
        :return:no return
        """
        best_host = ''
        best_time = 100
        with open(self.nodeFile, 'r') as node:
            host_list = list([n.strip() for n in node])
        resolve_hosts = set(host_list)
        if self.dnsFile and self.dns_timeout:
            print(u'DNS解析中...', end='', flush=True)
            resolve_hosts_list = self.dns_resolve()
            if debug:
                with open('debug.log','a+') as log:
                    log.write('resolve host: %s\nnode host: %s\n' % (str(resolve_hosts_list), str(resolve_hosts)))
            if resolve_hosts_list:
                resolve_hosts = set(host_list).union(resolve_hosts_list)

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.thread_count) as executor:
            future_results = {executor.submit(connect, host.strip(), self.connect_timeout, debug): host for host in resolve_hosts}
            for results in concurrent.futures.as_completed(future_results):
                item = results.result()
                if debug:
                    with open('debug.log','a+') as log:
                        log.write('get result, connected item: %s\n' % str(item))
                if item[1] and best_time > item[1]:
                    best_time = item[1]
                    best_host = item[0]

        if best_host == domain:
            print(u'当前解析节点速度最快，无需修改')
        else:
            print(u'\n连接最好的节点为: %s\n连接速度为: %d毫秒' % (best_host, best_time))
            print(u'建议在系统hosts文件添加: %s client-onisoul.86joy.com\n' % best_host)

    def dns_resolve(self):
        """DNS resolve domain name with dns server offered by dnsFile, return all resovled hosts' ip addresses
        :return: resolved hosts' ip addresses set
        :type return: set
        """
        dns_hosts = set()
        with open(self.dnsFile, 'r') as dnsfile:
            dnsnodes = dnsfile.readlines()

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.thread_count) as executor:
            future_results = {executor.submit(resolve, node.strip(), self.dns_timeout, debug): node for node in dnsnodes}
            for results in concurrent.futures.as_completed(future_results):
                print('.', end='', flush=True)
                item = set(results.result())
                dns_hosts = dns_hosts.union(item)
                if debug:
                    with open('debug.log','a+') as log:
                        log.write('get result, resolved item:%s, resolved item list %s\n' %  (str(item), str(dns_hosts)))
        print('')
        return dns_hosts

def connect(host, timeout, debug=False):
    """Connect single host and get the connected time, return (host, connected time) tuple
    :param host: ip address or domain name for http access
    :type host:string, must be ip address format or domain name format
    :param timeout:http connect timeout value with unit of second
    :type timeout: int
    :param debug: write debug log or not
    :type debug: bool
    :return: host and connected time
    :type return: tuple
    """
    conn = http.client.HTTPConnection(host, 80, timeout=timeout)
    end_time = 0
    try:
        start_time = time.clock()
        conn.request('GET', url, '', headers)
        crawl_rep = conn.getresponse()
        if not crawl_rep.status == 200:
            raise http.client.HTTPException
        end_time = (time.clock()-start_time) * 1000
    except (http.client.HTTPException, IOError):
        print(u'%s连接失败'% host)
    else:
        print(u'%s连接速度为%d毫秒'% (host, end_time))
    finally:
        conn.close()
    return (host, end_time)

def resolve(node, timeout, debug=False):
    """Resolve domain name with single dns server and return the resolved hosts set
    :param node: dns server for resolving domain name
    :type node: string, must be ip address format
    :param timeout: dns resolve timeout value with unit of second
    :type timeout: int
    :param debug: write debug log or not
    :type debug: bool
    :return: resolved hosts set
    :type return: set
    """
    message = dns.message.make_query(domain, 'A')
    host = []
    try:
        respond = dns.query.udp(message, node, timeout)
    except(dns.query.BadResponse, dns.query.UnexpectedSource, dns.exception.Timeout):
        with open('error.log','a+') as error:
            error.write('DNS Server %s resolve failed\n' % node)
    else:
        for answer in respond.answer:
            arecord = re.findall(r'IN A (\d+\.\d+\.\d+\.\d+)', str(answer))
            if arecord:
                host.extend(arecord)
            else:
                '''
                When running in windows system and convert the code to exe by cx_Freeze,
                the ip address in returned string value of "answer" turn to hex.Don't konw
                why, but for keeping the code running well, I add these codes below.
                '''
                arecord_hex = re.findall(r'IN A \\# 4 (\w+)', str(answer))
                for hex in arecord_hex:
                    try:
                        a = binascii.unhexlify(hex)
                        s = socket.inet_ntoa(a)
                    except TypeError:
                        with open('error.log','a+') as error:
                            error.write('type error %s answer %s\n' % (hex, str(answer)))
                    else:
                        host.append(s)
    if debug:
        with open('debug.log','a+') as log:
            log.write('DNS Server %s resolve host list: %s\n' % (node, host))
    return set(host)

def main():
    """Main function that get the global setting and run the module class and its methods
    :return: no return
    """
    config = configparser.ConfigParser()
    if not os.path.exists('setting.cfg') or not os.path.isfile('setting.cfg'):
        print(u'全局配置setting.cfg文件不存在\n')
    else:
        config.read('setting.cfg','utf-8')
        #check if debug enable
        if config.has_option('DEBUG', 'enable') and config['DEBUG']['enable'] and config['DEBUG']['enable'] == '1':
            global debug
            debug = True
        print('debug:', 'enable' if debug else 'disable')
        #http headers setting
        if config.has_section('HEADERS') and config.options('HEADERS').__len__()>0:
            global headers
            headers = dict()
            for key in config.options('HEADERS'):
                if config['HEADERS'][key]:
                    headers[key] = config['HEADERS'][key]
            if debug:
                print('headers',headers)
        #url postfix setting
        if config.has_option('URL', 'url') and config['URL']['url']:
             global url
             url = config['URL']['url']
             if debug:
                print('url',url)
        #domain name setting
        if config.has_option('DOMAIN', 'domain') and config['DOMAIN']['domain']:
            global domain
            domain = config['DOMAIN']['domain']
            if debug:
                print('domain',domain)
        resolve = set()

        #DNS Module Setting
        if config.has_option('DNS','enable') and config['DNS']['enable'] == '1':
            dnsFile = 'dns.cfg'
            dns_timeout = 5
            if config.has_option('DNS', 'file') and config['DNS']['file']:
                dnsFile = config['DNS']['file']
                if not os.path.exists(dnsFile) or not os.path.isfile(dnsFile):
                    del dnsFile
                    print(u'DNS模块%s配置文件不存在\n' % dnsFile)
                if debug:
                    print('dnsFile',dnsFile)
            if config.has_option('DNS', 'timeout') and config['DNS']['timeout']:
                dns_timeout = int(config['DNS']['timeout']) if int(config['DNS']['timeout'])>0 else 5
                if debug:
                    print('dns_timeout',dns_timeout)

        #HTTP Connect Module Setting
        nodeFile = 'node.cfg'
        connect_timeout = 5
        if config.has_option('CONNECT', 'file') and config['CONNECT']['file']:
            nodeFile = config['CONNECT']['file']
        if os.path.exists(nodeFile) and os.path.isfile(nodeFile):
            if debug:
                print('nodeFile',nodeFile)
        else:
            print(u'CONNECT模块%s配置文件不存在' % dnsFile)
            return
        if config.has_option('CONNECT', 'timeout') and config['CONNECT']['timeout']:
            connect_timeout = int(config['CONNECT']['timeout']) if int(config['CONNECT']['timeout'])>0 else 5
            if debug:
                print('connect_timeout',connect_timeout)
        cdn = CDNTEST(dnsFile, dns_timeout, nodeFile, connect_timeout)
        cdn.host_connect()

if __name__ == '__main__':
    multiprocessing.freeze_support()
    main()
    input('\nPause...')
