#!/usr/bin/python

"""
http://www.multipath-tcp.org/


http://mininet.org/api/classmininet_1_1net_1_1Mininet.html
https://github.com/mininet/mininet/blob/master/mininet/node.py

https://www.wireshark.org/docs/man-pages/tshark.html
https://www.wireshark.org/docs/dfref/t/tcp.html
http://www.packetlevel.ch/html/tcpdumpf.html
tshark -G | grep Multipath

https://iperf.fr/iperf-doc.php
https://github.com/ouya/iperf/

https://docs.python.org/2/library/xml.etree.elementtree.html
http://effbot.org/downloads#elementtree
"""

"""
questions:
 - what is a mininet.controller (c0)? why it's not working without that?
 - why are host trend to be behind a switch?
 - how to meansure/monitor bandwith/delay?
 - iperf 'Connection refused' sometimes...
 - double delay on the first ping
 - iperf freeze if swith's interface turn down, but good handover if host's intf down
 - mininet learn between runs, ping breaks arp/handover ?!?!?!?!?!?!?!???
 - 

Notes:
 - run program on a host: run long process at background and pipe it's output to file, so other short processes can run meanwhile (sendCmd don't block the caller script, but sets waiting to True)

TODO:
 - meansure delay, and bandwidth more frequency

"""

import time
import os
import re
import xml.etree.ElementTree
from mininet.net import Mininet
from mininet.link import TCLink
#from mininet.util import custom

test_ping = False
test_bandwith = True
capture_mptcp_headers = True
cut_a_link = True
ping_test_count = 3
bandwith_test_duration = 10 # seconds
num_subflows = 1 # create multiple subflows for each pair of IP-addresses (with a different port)

os.system('echo '+str(num_subflows)+' | sudo tee /sys/module/mptcp_fullmesh/parameters/num_subflows')

net = Mininet( cleanup=True )

h1 = net.addHost( 'h1', ip='10.0.1.1')
h2 = net.addHost( 'h2', ip='10.0.2.1')

s11 = net.addSwitch( 's11' )
s12 = net.addSwitch( 's12' )
s13 = net.addSwitch( 's13' )
s2 = net.addSwitch( 's2' )

c0 = net.addController( 'c0' )

#clink = custom(TCLink, bw=10, delay='10ms')
#link = net.addLink( h1, h2, cls=clink)
link11 = net.addLink( h1, s11, cls=TCLink , bw=50, delay='10ms' )
link12 = net.addLink( h1, s12, cls=TCLink , bw=50, delay='10ms' )
link13 = net.addLink( h1, s13, cls=TCLink , bw=50, delay='10ms' )
link2 = net.addLink( h2, s2, cls=TCLink , bw=50, delay='10ms' )
link3 = net.addLink( s11, s2, cls=TCLink , bw=20, delay='1ms' )
link4 = net.addLink( s12, s2, cls=TCLink , bw=5, delay='100ms' )
link5 = net.addLink( s13, s2, cls=TCLink , bw=10, delay='100ms' )
#h1.setIP('10.0.1.1', intf='h1-eth0')
h1.setIP('10.0.1.2', intf='h1-eth1')
h1.setIP('10.0.1.3', intf='h1-eth2')
#h2.setIP('10.0.2.1', intf='h2-eth0')
#print h1.intf('h1-eth0').updateIP()

net.start()

print "\n"," "*5,"#"*40,"\n"," "*10,"STARTING\n"

#print net.hosts
#print net.switches
#print net.controllers
#print net.links
#print net.nameToNode
print
# https://github.com/mininet/mininet/blob/master/mininet/util.py#L240
for node in net.items():
    #print repr(node[1])
    print node[1]
    for intf in node[1].intfList():
        print "\t"+str(intf)+":"+str(intf.IP()),
        if intf.link:
            intf2 = intf.link.intf2 if intf==intf.link.intf1 else intf.link.intf1
            print "\t<->\t"+str(intf2)+":"+str(intf2.IP()),
        print
    print "\n",
print
#for i in (net.links):
#    print i
#print


if test_ping:
    #print net.pingFull()
    print h1.cmd('ping -c '+str(ping_test_count)+' -I h1-eth0 '+h2.IP())
    print h1.cmd('ping -c '+str(ping_test_count)+' -I h1-eth1 '+h2.IP())
    print h2.cmd('ping -c '+str(ping_test_count)+' -I h2-eth0 '+h1.intf('h1-eth0').IP())
    print h2.cmd('ping -c '+str(ping_test_count)+' -I h2-eth0 '+h1.intf('h1-eth1').IP())
    #print h1.cmd('ping -c '+str(ping_test_count)+' -I h1-eth0 '+h2.IP())

if capture_mptcp_headers:
    print "starting capturing...",
    #h1.cmd('tshark -i h1-eth0 -a duration:'+str(bandwith_test_duration)+' -c 1 -f "tcp" -V &>capt.txt & sleep 1')
    #h1.cmd('tshark -i h1-eth0 -a duration:'+str(bandwith_test_duration)+' -c 100 -f "tcp" -T fields -e ip.src -e ip.dst -e tcp.srcport -e tcp.dstport -e tcp.option_kind -e tcp.options.mptcp.subtype &>capt.txt & sleep 1')
    #h1.cmd('tshark -i h1-eth0 -a duration:'+str(bandwith_test_duration)+' -c 100 -f "tcp" -T pdml &>capt.txt & sleep 1')
    #print h2.cmd('tshark -f "tcp" -i any -a duration:'+str(bandwith_test_duration+2)+' -c 1000 -T pdml &>capt.txt &'),
    print h2.cmd('tshark -f "tcp" -i any -a duration:'+str(bandwith_test_duration+1)+' -T pdml | '+
                    'sed -e "s/30313233343536373839//g" | '+
                    'sed -e "s/30:31:32:33:34:35:36:37:38:39://g" >capt.txt &'),
    time.sleep(1) # wait for tshark to startup
    print '...capture started',"\n"

if test_bandwith:
    # iperf test
    print 'starting iperf server at',h2.IP()
    h2.cmd('iperf -s -i 0.5 > iperf_server_log.txt & ') # server
    
    print 'starting iperf client at',h1.IP(),', connect to ',h2.IP()
    #iperf_client_options = '-n 1 -l 24'
    #iperf_client_options = '-t '+str(bandwith_test_duration)+' -i 0.5 -y c'
    iperf_client_options = '-t '+str(bandwith_test_duration)+' -i 0.5 '
    test_started_timestamp = time.time()
    #print "\niperf client response:\n",h1.cmd('iperf '+iperf_client_options+' -c '+h2.IP()) # cliens
    h1.cmd('iperf '+iperf_client_options+' -c '+h2.IP()+' > iperf_client_log.txt &') # cliens
    
    if cut_a_link:
        time.sleep(bandwith_test_duration/6.0*2.0)
        print "\n",'cutting link...',
        #print h1.intf('h1-eth0').ifconfig('down'),
        print h1.intf('h1-eth1').ifconfig('down'),
        #print h1.intf('h1-eth1').ifconfig('up'),
        #print s11.intf('s11-eth1').ifconfig('down'),
        #print s12.intf('s12-eth2').ifconfig('down'),
        #print s12.intf('s12-eth1').ifconfig('down'),
        #print s2.intf('s2-eth3').ifconfig('down'),
        print 'link down',
        time.sleep(bandwith_test_duration/6.0*4.0)
        print
    else:
        time.sleep(bandwith_test_duration)
    time.sleep(1) # wait a bit to finish
    
    print "\niperf client response:"
    print h1.cmd('cat iperf_client_log.txt')
    
    print "\niperf server response:"
    print h2.cmd('cat iperf_server_log.txt')

if capture_mptcp_headers:
    try:
        time.sleep(0.5)
        # parse result
        capture_data = h1.cmd('cat capt.txt')
        capture_data = capture_data[ capture_data.find('<pdml') : ]
        capture_data = re.findall( r"<packet>.+?</packet>", capture_data, re.DOTALL)
        print "capturing ended, result ("+str(len(capture_data))+"):"
        for i in capture_data:
            packet = xml.etree.ElementTree.fromstring(i)
            packet_timestamp = packet.find('proto[@name="geninfo"]').find('field[@name="timestamp"]').get('value')
            ip_header = packet.find('proto[@name="ip"]')
            tcp_header = packet.find('proto[@name="tcp"]')
            src_ip = ip_header.find('field[@name="ip.src"]').get('show')
            dst_ip = ip_header.find('field[@name="ip.dst"]').get('show')
            src_port = tcp_header.find('field[@name="tcp.srcport"]').get('show')
            dst_port = tcp_header.find('field[@name="tcp.dstport"]').get('show')
            package_info = ("%.2f" % (float(packet_timestamp)-test_started_timestamp)) +"\t"+src_ip+':'+src_port+"\t->\t"+dst_ip+':'+dst_port+"\t"
            allmptcp = tcp_header.findall('field[@name="tcp.options"]/*/field[@name="tcp.option_kind"][@show="30"]/..')
            mptcp_subtypes = []
            for mptcp in allmptcp:
                package_info = package_info + mptcp.get('show') + "\t"
                mptcp_subtype = mptcp.find('field[@name="tcp.options.mptcp.subtype"]').get('value')
                mptcp_subtypes.append( mptcp_subtype )
                package_info = package_info + '(subtype: '+mptcp_subtype
                if mptcp_subtype == '1': # Join connection
                    addrid = mptcp.find('field[@name="tcp.options.mptcp.addrid"]')
                    if addrid != None:
                        package_info = package_info + ', addrid: '+addrid.get('value')
                if mptcp_subtype == '3': # Add Address
                    addrid = mptcp.find('field[@name="tcp.options.mptcp.addrid"]')
                    if addrid != None:
                        package_info = package_info + ', addrid: '+addrid.get('value')
                    newaddripv4 = mptcp.find('field[@name="tcp.options.mptcp.ipv4"]')
                    if newaddripv4 != None:
                        package_info = package_info + ', ipv4: '+newaddripv4.get('show')
                package_info = package_info + ' )' + "\t"
            if len(mptcp_subtypes)==0 or ( len(mptcp_subtypes)==1 and mptcp_subtypes[0]=='2' ):
                continue # skip packet contains only data, not interesting
                pass
            print package_info
            try:
                safety = safety+1
            except NameError:
                safety = 0
            if safety > 300:
                print 'safety>100'
                break
            #xml.etree.ElementTree.dump(mptcp)
    except Exception as e:
        print "\n\nERROR:",e,"\n\n"


net.stop()

print








