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
 - what is a mininet.controller (c0)?                                                                                                                                                                            
 - why are host trend to be behind a switch?                                                                                                                                                                     
 - how to meansure/monitor?                                                                                                                                                                                      
 - iperf 'Connection refused' sometimes...                                                                                                                                                                       
 -                                                                                                                                                                                                               
"""

import time
import xml.etree.ElementTree
from mininet.net import Mininet

capture_mptcp_headers = False
capture_duration = 2 # seconds

net = Mininet( cleanup=True )

h1 = net.addHost( 'h1' )
h2 = net.addHost( 'h2' )

#s1 = net.addSwitch( 's1' )
#s2 = net.addSwitch( 's2' )

#c0 = net.addController( 'c0' )

net.addLink( h1, h2) # TODO set bw, delay

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
        print "\t%s\t<->\t" % intf,
        if intf.link:
            print (intf.link.intf2 if intf==intf.link.intf1 else intf.link.intf1),
    print "\n"
print
#for i in (net.links):
#    print i
#print

#print 'h1 ifconfig:'
#print h1.cmd('ifconfig -a')

if capture_mptcp_headers:
    print "starting capturing...",
    #h1.cmd('tshark -i h1-eth0 -a duration:'+str(capture_duration)+' -c 1 -f "tcp" -V &>capt.txt & sleep 1')
    #h1.cmd('tshark -i h1-eth0 -a duration:'+str(capture_duration)+' -c 100 -f "tcp" -T fields -e ip.src -e ip.dst -e tcp.srcport -e tcp.dstport -e tcp.option_kind -e tcp.options.mptcp.subtype &>capt.txt & sleep 1')
    h1.cmd('tshark -i h1-eth0 -a duration:'+str(capture_duration)+' -c 5 -f "tcp" -T pdml &>capt.txt & sleep 1')
    print 'capture started',"\n"

# iperf test
print 'starting iperf server at',h2.IP()
h2.sendCmd('iperf -s ') # server

print 'starting iperf client at',h1.IP(),', connect to ',h2.IP()
iperf_client_options = '-n 1 -l 24'
iperf_client_options = '-t 5 -i 0.5 -y c'
iperf_client_options = '-t 5 -i 0.5 '
print "\niperf client response:\n",h1.cmd('iperf '+iperf_client_options+' -c '+h2.IP()) # cliens

print "\niperf server response:"
print h2.monitor()
h2.sendInt() # interrupt
print h2.waitOutput()

if capture_mptcp_headers:
    time.sleep(capture_duration+0.1)
    print "capturing ended, result:"
    # parse result
    capture_data = h1.cmd('cat capt.txt')
    capture_data = capture_data[ capture_data.find('<pdml') : ]
    capture_data = xml.etree.ElementTree.fromstring(capture_data)
    for packet in capture_data:
        ip_header = packet.find('proto[@name="ip"]')
        tcp_header = packet.find('proto[@name="tcp"]')
        src_ip = ip_header.find('field[@name="ip.src"]').get('show')
        dst_ip = ip_header.find('field[@name="ip.dst"]').get('show')
        src_port = tcp_header.find('field[@name="tcp.srcport"]').get('show')
        dst_port = tcp_header.find('field[@name="tcp.dstport"]').get('show')
        mptcp = tcp_header.find('field[@name="tcp.options"]/*/field[@name="tcp.option_kind"][@show="30"]/..')
        print src_ip+':'+src_port+"\t->\t"+dst_ip+':'+dst_port+"\t",
        print mptcp.get('show')
        #xml.etree.ElementTree.dump(mptcp)

#net.interact()

net.stop()










