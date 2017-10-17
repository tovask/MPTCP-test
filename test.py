#!/usr/bin/python

"""
http://mininet.org/api/classmininet_1_1net_1_1Mininet.html
https://github.com/mininet/mininet/blob/master/mininet/node.py
https://www.wireshark.org/docs/man-pages/tshark.html
https://iperf.fr/iperf-doc.php
"""

import time

from mininet.net import Mininet

net = Mininet( cleanup=True )

h1 = net.addHost( 'h1' )
h2 = net.addHost( 'h2' )

#s1 = net.addSwitch( 's1' )
#s2 = net.addSwitch( 's2' )

#c0 = net.addController( 'c0' )

net.addLink( h1, h2 )

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
"""https://github.com/mininet/mininet/blob/master/mininet/util.py#L240"""
for node in net.items():
    #print repr(node[1])
    print node[1]
    for intf in node[1].intfList():
        print "\t%s\t<->\t" % intf,
        if intf.link:
            intfs = [ intf.link.intf1, intf.link.intf2 ]
            intfs.remove( intf )
            print intfs[ 0 ],
    print "\n"
print
#for i in (net.links):
#    print i
#print

#print 'h1 ifconfig:'
#print h1.cmd('ifconfig -a')
print "capturing starting"
capture_duration = 2 # seconds
#h1.cmd('tshark -i h1-eth0 -a duration:'+str(capture_duration)+' >capt.txt &')
h1.cmd('tshark -i h1-eth0 -a duration:'+str(capture_duration)+' >capt.txt & sleep 1')
#net.pingAll()
#time.sleep(capture_duration+1)
#print "capturing ended\nresult:"
#print h1.cmd('cat capt.txt')

# iperf test
print 'starting server'
h2.sendCmd('iperf -s ') # server

print 'start client to ',h2.IP()
print h1.cmd('iperf -n 1 -l 4 -c '+h2.IP()) # cliens

print "\nserver response:"
print h2.monitor()
h2.sendInt() # interrupt
print h2.waitOutput()

time.sleep(capture_duration+1)
print "capturing ended\nresult:"
print h1.cmd('cat capt.txt')

#net.interact()

net.stop()