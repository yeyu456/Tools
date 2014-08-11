# -*- coding: utf-8 -*-
import http.client
import time
import dns.query, dns.message, dns.exception, dns.rrset, dns.name
import re
import multiprocessing
from multiprocessing import pool
import configparser
import os.path

#default global setting
headers = {'Host' : 'client-onisoul.86joy.com',
           'Connection' : 'keep-alive',
           'Referer' : 'http://game-onisoul.86joy.com/client/app.unity3d?revision=30672007',
           'User-Agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.125 Safari/537.36',
           'Accept-Encoding' : 'gzip,deflate,sdch',
           'Accept-Language' : 'zh-CN,zh;q=0.8,en;q=0.6,ja;q=0.4,ko;q=0.2,zh-TW;q=0.2'}
url = '/crossdomain.xml'
domain = 'client-onisoul.86joy.com'
debug = False

class CDNTEST(object):
    def __init__(self):
        super(CDNTEST, self).__init__()

    def host_connect(self, resolve_hosts, nodeFile, timeout):
        """Connect all nodes and resolved nodes to get the connecting time and print the least one
        :param resolve_hosts: resolved hosts set,which provided by dns_resolve method
        :type resolve_hosts: set
        :param nodeFile: file that stores cdn nodes' ip addresses
        :type nodeFile: string or file object same as open()
        :param timeout:http connect timeout value with unit of second
        :type timeout: int
        :return:no return
        """
        best_host = ''
        best_time = 100
        connect_pool = pool.Pool(processes=multiprocessing.cpu_count())
        cq = multiprocessing.Manager().Queue()

        with open(nodeFile, 'r') as node:
            host_list = [n.strip() for n in node]
        if debug:
            print('resolve host: %s\nnode host: %s\n' % (list(resolve_hosts), host_list))
            print('resolve hosts different from node.cfg with set : ',list(resolve_hosts.difference(set(host_list))))
        resolve_hosts = set(host_list).union(resolve_hosts)

        for host in resolve_hosts:
            host = host.strip()
            connect_pool.apply_async(connect, args=(host, timeout, cq, debug))

        for n in range(resolve_hosts.__len__()):
            item = cq.get(True)
            if debug:
                print('pop queue, connected item: ',item)
            if item[1] and best_time > item[1]:
                best_time = item[1]
                best_host = item[0]

        if best_host == domain:
            print(u'当前解析节点速度最快，无需修改')
        else:
            print(u'\n连接最好的节点为: %s\n连接速度为: %d毫秒' % (best_host, best_time))
            print(u'建议在系统hosts文件添加: %s client-onisoul.86joy.com\n' % best_host)

    def dns_resolve(self, dnsFile, timeout):
        """DNS resolve domain name with dns server offered by dnsFile, return all resovled hosts' ip addresses
        :param dnsFile: file that stores all isp dns server ip address
        :type dnsFile: string or file object same as open()
        :param timeout: dns resolve timeout value with unit of second
        :type timeout: int
        :return: resolved hosts' ip addresses set
        :type return: set
        """
        dns_hosts = set()
        dns_pool = pool.Pool(processes=multiprocessing.cpu_count())
        with open(dnsFile, 'r') as dnsfile:
            dnsnodes = dnsfile.readlines()

        q = multiprocessing.Manager().Queue()
        for node in dnsnodes:
            dns_pool.apply_async(resolve, args=(node.strip(), timeout, q, debug))
        dns_pool.close()
        dns_pool.join()
        for n in range(dnsnodes.__len__()):
            dns_hosts = dns_hosts.union(q.get(True))
            if debug:
                print('pop queue, resolved item:', dns_hosts)
        return dns_hosts

def connect(host, timeout, cq, debug=False):
    """Connect single host and get the connected time, put (host, connected time) tuple in process shared queue
    :param host: ip address or domain name for http access
    :type host:string, must be ip address format or domain name format
    :param timeout:http connect timeout value with unit of second
    :type timeout: int
    :param cq: multiple processes shared queue for item with (host, connected time) tuple
    :type cq: Queue
    :return:no return
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
        print(u'\t%s连接失败'% host)
    else:
        print(u'\t%s连接速度为%d毫秒'% (host, end_time))
    finally:
        conn.close()
    print(host, end_time)
    cq.put((host, end_time))

def resolve(node, timeout, q, debug=False):
    """Resolve domain name with single dns server and put the resolved hosts set in process shared queue
    :param node: dns server for resolving domain name
    :type node: string, must be ip address format
    :param timeout: dns resolve timeout value with unit of second
    :type timeout: int
    :param q: multiple processes shared queue for resolved hosts set
    :type q: Queue
    :return: no return
    """
    message = dns.message.make_query(domain, 'A')
    host = set()
    try:
        respond = dns.query.udp(message, node, timeout)
    except(dns.query.BadResponse, dns.query.UnexpectedSource, dns.exception.Timeout):
        print('DNS Server %s resolve failed' % node)
    else:
        for answer in respond.answer:
            arecord = re.findall(r'IN A (\d+\.\d+\.\d+\.\d+)', str(answer))
            if arecord:
                host = host.union(set(arecord))
    if debug:
        print('DNS Server %s resolve host list: %s' % (node, list(host)))
    q.put(host)

def main():
    """Main function that get the global setting and run the module class and its methods
    :return: no return
    """
    config = configparser.ConfigParser()
    if not os.path.exists('setting.cfg') or not os.path.isfile('setting.cfg'):
        print(u'全局配置setting.cfg文件不存在')
    else:
        config.read('setting.cfg','utf-8')
        #check if debug enable
        if config.has_option('DEBUG', 'enable') and config['DEBUG']['enable'] and config['DEBUG']['enable'] == '1':
            global debug
            debug = True
            print('debug',debug)
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
        gwz = CDNTEST()
        resolve = set()

        #DNS Module Setting
        if config.has_option('DNS','enable') and config['DNS']['enable'] == '1':
            dnsFile = 'dns.cfg'
            dns_timeout = 5
            if config.has_option('DNS', 'file') and config['DNS']['file']:
                dnsFile = config['DNS']['file']
                if debug:
                    print('dnsFile',dnsFile)
            if config.has_option('DNS', 'timeout') and config['DNS']['timeout']:
                dns_timeout = int(config['DNS']['timeout']) if int(config['DNS']['timeout'])>0 else 5
                if debug:
                    print('dns_timeout',dns_timeout)
            if os.path.exists(dnsFile) and os.path.isfile(dnsFile):
                resolve = gwz.dns_resolve(dnsFile, dns_timeout)
            else:
                print(u'DNS模块%s配置文件不存在' % dnsFile)

        #HTTP Connect Module Setting
        nodeFile = 'node.cfg'
        connect_timeout = 5
        if config.has_option('CONNECT', 'file') and config['CONNECT']['file']:
            tmpFile = config['CONNECT']['file']
            if os.path.exists(tmpFile) and os.path.isfile(tmpFile):
                nodeFile = tmpFile
                del tmpFile
                if debug:
                    print('nodeFile',nodeFile)
        if config.has_option('CONNECT', 'timeout') and config['CONNECT']['timeout']:
            connect_timeout = int(config['CONNECT']['timeout']) if int(config['CONNECT']['timeout'])>0 else 5
            if debug:
                print('connect_timeout',connect_timeout)
        gwz.host_connect(resolve, nodeFile, connect_timeout)

    input('\nPause...')

if __name__ == '__main__':
    multiprocessing.freeze_support()
    main()