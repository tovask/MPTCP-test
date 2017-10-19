#!/usr/bin/python

"""
http://mininet.org/api/classmininet_1_1net_1_1Mininet.html
https://github.com/mininet/mininet/blob/master/mininet/node.py

https://www.wireshark.org/docs/man-pages/tshark.html
https://www.wireshark.org/docs/dfref/t/tcp.html
http://www.packetlevel.ch/html/tcpdumpf.html
tshark -G | grep Multipath

https://iperf.fr/iperf-doc.php
https://github.com/ouya/iperf/
"""

"""
questions:
 - what is a mininet.controller (c0)? why it's not working without that?
 - why are host trend to be behind a switch?
 - how to meansure/monitor bandwith/delay?
 - iperf 'Connection refused' sometimes...
 - double delay on the first ping
 - 
"""
"""
TODO:
 - mptcp headers findAll (not just one)
 - echo 3 | sudo tee /sys/modules/mptcp_ ...
 - cut a link while meansuring
"""

import time
import xml.etree.ElementTree
from mininet.net import Mininet
from mininet.link import TCLink
#from mininet.util import custom

test_ping = True
test_bandwith = True
capture_mptcp_headers = True
ping_test_count = 3
bandwith_test_duration = 2 # seconds

net = Mininet( cleanup=True )

h1 = net.addHost( 'h1', ip='10.0.1.1')
h2 = net.addHost( 'h2', ip='10.0.2.1')

s11 = net.addSwitch( 's11' )
s12 = net.addSwitch( 's12' )
s2 = net.addSwitch( 's2' )

c0 = net.addController( 'c0' )

#clink = custom(TCLink, bw=10, delay='10ms')
#link = net.addLink( h1, h2, cls=clink)
link11 = net.addLink( h1, s11, cls=TCLink , bw=50, delay='10ms' )
link12 = net.addLink( h1, s12, cls=TCLink , bw=50, delay='10ms' )
link2 = net.addLink( h2, s2, cls=TCLink , bw=50, delay='10ms' )
link3 = net.addLink( s11, s2, cls=TCLink , bw=10, delay='10ms' )
link4 = net.addLink( s12, s2, cls=TCLink , bw=10, delay='10ms' )
#h1.setIP('10.0.1.1', intf='h1-eth0')
h1.setIP('10.0.1.2', intf='h1-eth1')
#h2.setIP('10.0.2.1', intf='h2-eth0')
#print h1.intf('h1-eth0').updateIP()
#print "\n",repr(link),"\n",vars(link),"\n"


#net.addLink( h1, h2)

#net.addLink( h1, s1 )
#net.addLink( h2, s2 )
#net.addLink( s1, s2 )

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
    print "\n"
print
#for i in (net.links):
#    print i
#print

if test_ping:
    #print net.pingFull()
    #print h1.cmd('ping -c '+str(ping_test_count)+' -I h1-eth0 '+h2.IP())
    print h1.cmd('ping -c '+str(ping_test_count)+' -I h1-eth1 '+h2.IP())
    print h2.cmd('ping -c '+str(ping_test_count)+' -I h2-eth0 '+h1.intf('h1-eth0').IP())
    #print h2.cmd('ping -c '+str(ping_test_count)+' -I h2-eth0 '+h1.intf('h1-eth1').IP())
    #print h1.cmd('ping -c '+str(ping_test_count)+' -I h1-eth0 '+h2.IP())

#print 'h1 ifconfig:'
#print h1.cmd('ifconfig -a')

if capture_mptcp_headers:
    print "starting capturing...",
    #h1.cmd('tshark -i h1-eth0 -a duration:'+str(bandwith_test_duration)+' -c 1 -f "tcp" -V &>capt.txt & sleep 1')
    #h1.cmd('tshark -i h1-eth0 -a duration:'+str(bandwith_test_duration)+' -c 100 -f "tcp" -T fields -e ip.src -e ip.dst -e tcp.srcport -e tcp.dstport -e tcp.option_kind -e tcp.options.mptcp.subtype &>capt.txt & sleep 1')
    #h1.cmd('tshark -i h1-eth0 -a duration:'+str(bandwith_test_duration)+' -c 100 -f "tcp" -T pdml &>capt.txt & sleep 1')
    h2.cmd('tshark -f "tcp" -i any -a duration:'+str(bandwith_test_duration)+' -c 1000 -T pdml &>capt.txt & sleep 1')
    print 'capture started',"\n"

if test_bandwith:
    # iperf test
    print 'starting iperf server at',h2.IP()
    h2.sendCmd('iperf -s ') # server
    
    print 'starting iperf client at',h1.IP(),', connect to ',h2.IP()
    iperf_client_options = '-n 1 -l 24'
    iperf_client_options = '-t '+str(bandwith_test_duration)+' -i 0.5 -y c'
    iperf_client_options = '-t '+str(bandwith_test_duration)+' -i 0.5 '
    print "\niperf client response:\n",h1.cmd('iperf '+iperf_client_options+' -c '+h2.IP()) # cliens
    
    print "\niperf server response:"
    print h2.monitor()
    h2.sendInt() # interrupt
    print h2.waitOutput()

if capture_mptcp_headers:
    time.sleep(bandwith_test_duration+0.1)      # make sure the testing ended
    # parse result
    capture_data = h1.cmd('cat capt.txt')
    capture_data = capture_data[ capture_data.find('<pdml') : ]
    capture_data = xml.etree.ElementTree.fromstring(capture_data)
    print "capturing ended, result ("+str(len(capture_data))+"):"
    for packet in capture_data:
        ip_header = packet.find('proto[@name="ip"]')
        tcp_header = packet.find('proto[@name="tcp"]')
        src_ip = ip_header.find('field[@name="ip.src"]').get('show')
        dst_ip = ip_header.find('field[@name="ip.dst"]').get('show')
        src_port = tcp_header.find('field[@name="tcp.srcport"]').get('show')
        dst_port = tcp_header.find('field[@name="tcp.dstport"]').get('show')
        mptcp = tcp_header.find('field[@name="tcp.options"]/*/field[@name="tcp.option_kind"][@show="30"]/..')
        print src_ip+':'+src_port+"\t->\t"+dst_ip+':'+dst_port+"\t",
        if mptcp != None:
            print mptcp.get('show'),
            mptcp_subtype = mptcp.find('field[@name="tcp.options.mptcp.subtype"]').get('value')
            print '(subtype:',mptcp_subtype,')',
            if mptcp_subtype == '1': # Join connection
                addrid = mptcp.find('field[@name="tcp.options.mptcp.addrid"]')
                if addrid != None:
                    print '(addrid:',addrid.get('value'),')',
        print
        #xml.etree.ElementTree.dump(mptcp)

#net.interact()

net.stop()










