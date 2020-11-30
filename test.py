#!/usr/bin/env python

"""
Start up a Simple topology for CS144
"""

import sys
import mininet.net
import mininet.node

from mininet.log import setLogLevel, info
from mininet.cli import CLI
from mininet.topo import Topo
from mininet.util import quietRun
from mininet.moduledeps import pathCheck
import re

from sys import exit
import os.path
from subprocess import Popen, STDOUT, PIPE, check_call

IPBASE = '10.3.0.0/16'
ROOTIP = '10.3.0.100/16'
IPCONFIG_FILE = './IP_CONFIG'
IP_SETTING={}

class TwoServerClientAndRouterTopology(Topo):
    "Topology with 2 servers and 1 client connected with a switch/router"

    def __init__( self, *args, **kwargs ):
        Topo.__init__( self, *args, **kwargs )
        server1 = self.addHost( 'server1' )
        server2 = self.addHost( 'server2' )
        router = self.addSwitch( 'sw0' )
        client = self.addHost('client')
        for h in server1, server2, client:
            self.addLink( h, router )

def set_default_route(host):
    info('*** setting default gateway of host %s\n' % host.name)
    if(host.name == 'server1'):
        routerip = IP_SETTING['sw0-eth1']
    elif(host.name == 'server2'):
        routerip = IP_SETTING['sw0-eth2']
    elif(host.name == 'client'):
        routerip = IP_SETTING['sw0-eth3']
    print host.name, routerip
    host.cmd('route add %s/32 dev %s-eth0' % (routerip, host.name))
    host.cmd('route add default gw %s dev %s-eth0' % (routerip, host.name))
    ips = IP_SETTING[host.name].split(".")
    host.cmd('route del -net %s.0.0.0/8 dev %s-eth0' % (ips[0], host.name))

def set_default_route_client(host):
    info('*** setting default gateway of client %s\n' % host.name)
    routerip = IP_SETTING['sw0-eth3']
    print host.name, routerip
    for eth in ['sw0-eth1', 'sw0-eth2', 'sw0-eth3']:
        swip = IP_SETTING[eth]
        pref = ".".join(swip.split(".")[:-1]) + ".0"
        print pref
        check_call('route add -net %s/24 gw 10.0.1.1 dev client-eth0' % (pref), shell = True)

def get_ip_setting():
    try:
        with open(IPCONFIG_FILE, 'r') as f:
            for line in f:
                if( len(line.split()) == 0):
                  break
                name, ip = line.split()
                print name, ip
                IP_SETTING[name] = ip
            info( '*** Successfully loaded ip settings for hosts\n %s\n' % IP_SETTING)
    except EnvironmentError:
        exit("Couldn't load config file for ip addresses, check whether %s exists" % IPCONFIG_FILE)

def starthttp( host ):
    "Start simple Python web server on hosts"
    info( '*** Starting SimpleHTTPServer on host', host, '\n' )
    host.cmd( 'cd ./http_%s/; nohup python2.7 ./webserver.py &' % (host.name) )


def stophttp():
    "Stop simple Python web servers"
    info( '*** Shutting down stale SimpleHTTPServers', 
          quietRun( "pkill -9 -f SimpleHTTPServer" ), '\n' )    
    info( '*** Shutting down stale webservers', 
          quietRun( "pkill -9 -f webserver.py" ), '\n' )   

def test_ping(infoStr,client,ip,flag=True,strict_mode = False):
    print(infoStr)
    res=client.cmd("ping -c 4",ip)

    if strict_mode:
        if not test_icmp_seq(res):
            print("Icmp Seq not correct!")
            print(res)
            return 5

    loss = int(re.search("(\d+)% packet loss",res).group(1));
    if loss==0 and flag:
        print("Success!")
        return 0
    elif loss==100 and not flag:
        print("Success!")
        return 0
    else:
        print("Error!!!")
        print(res)
        return 5

def test_icmp_seq(res):
    icmp_seqs = re.findall("icmp_seq=(\d)",res);
    if [int(x) for x in icmp_seqs] == [1,2,3,4]:
        return True
    else:
        return False

def test_traceroute(infoStr,client,target_ip,ips,strict_mode = False):
    print(infoStr)
    res=client.cmd("traceroute -m 3",target_ip)

    if strict_mode:
        if re.search("\*",res):
            print("Traceroute has unreachable measure!")
            print(res)
            return 5
    if re.search('!H',res):
        print("Error!!!")
        print(res)
        return 5
    res = ''.join(res.splitlines()[1:])
    for ip in ips:
        ip.replace(".","\.")
        if not re.search(ip,res):
            print("Error!!!")
            print(res)
            return 5
    print("Success!")
    return 0

def test_wget(infoStr,client,url,strict_mode = False):
    print(infoStr)
    res = client.cmd("wget",url)
    if not re.search("100%",res):
        print("Error!!!")
        print(res)
        return 5
    print("Success!")
    return 0

def main(args):
    "Create a simple network"
    get_ip_setting()
    topo = TwoServerClientAndRouterTopology()
    info( '*** Creating network\n' )
    net = mininet.net.Mininet(topo=topo, controller=mininet.node.RemoteController, ipBase=IPBASE )
    net.start()
    server1, server2, client, router = net.get( 'server1', 'server2', 'client', 'sw0')
    s1intf = server1.defaultIntf()
    s1intf.setIP('%s/8' % IP_SETTING['server1'])
    s2intf = server2.defaultIntf()
    s2intf.setIP('%s/8' % IP_SETTING['server2'])
    clintf = client.defaultIntf()
    clintf.setIP('%s/8' % IP_SETTING['client'])

    for host in server1, server2, client:
        set_default_route(host)
    # set_default_route_client(client)
    starthttp( server1 )
    starthttp( server2 )
    # CLI( net ,script="test.sh") 

    # total credit
    credit = 85
    strict_mode = False

    if(len(args)==2):
        if args[1]=='-s' or args[1]=='--strict':
            strict_mode = True
            print("Enable strict mode...")

    # test client ping router interface
    print("Start test ping...")
    deduction = test_ping("client ping 192.168.2.1",client,"192.168.2.1",strict_mode=strict_mode)
    credit-=deduction

    deduction = test_ping("client ping 172.64.3.1",client,"172.64.3.1",strict_mode=strict_mode)
    credit-=deduction

    deduction = test_ping("client ping 10.0.1.1",client,"10.0.1.1",strict_mode=strict_mode)
    credit-=deduction

    deduction = test_ping("client ping server1",client,server1.IP(),strict_mode=strict_mode)
    credit-=deduction

    deduction = test_ping("client ping server2",client,server2.IP(),strict_mode=strict_mode)
    credit-=deduction

    # test client ping error ip
    deduction = test_ping("client ping 192.168.2.3",client,"192.168.2.3",False,strict_mode=strict_mode)
    credit-=deduction

    # test client traceroute
    print("Start test traceroute...")
    deduction = test_traceroute("client traceroute 192.168.2.1",client,"192.168.2.1",["10.0.1.1"],strict_mode=strict_mode);
    credit-=deduction

    deduction = test_traceroute("client traceroute 172.64.3.1",client,"172.64.3.1",["10.0.1.1"],strict_mode=strict_mode);
    credit-=deduction

    deduction = test_traceroute("client traceroute 10.0.1.1",client,"10.0.1.1",["10.0.1.1"],strict_mode=strict_mode);
    credit-=deduction

    deduction = test_traceroute("client traceroute server1",client,server1.IP(),["10.0.1.1","192.168.2.2"],strict_mode=strict_mode);
    credit-=deduction

    deduction = test_traceroute("client traceroute server2",client,server2.IP(),["10.0.1.1","172.64.3.10"],strict_mode=strict_mode);
    credit-=deduction
    
    # test wget download file
    print("Start test wget...")
    deduction = test_wget("client wget http://192.168.2.2/index.html",client,"http://192.168.2.2/index.html",strict_mode=strict_mode)
    credit-=deduction

    deduction = test_wget("client wget http://172.64.3.10/index.html",client,"http://172.64.3.10/index.html",strict_mode=strict_mode)
    credit-=deduction

    print("Start test wget big file...")
    deduction = test_wget("client wget http://192.168.2.2/tmp",client,"http://192.168.2.2/tmp",strict_mode=strict_mode)
    credit-=deduction

    print("Congratulations: Your credit is {}".format(credit))
    
    stophttp()
    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    main(sys.argv)
