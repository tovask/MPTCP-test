#!/usr/bin/python
import os
import sys
import time
import subprocess
import re
import plotly	# https://plot.ly/python/reference/#scatter


debug = False

def parse_csv(file):
	rawres = ''
	with open(file, 'r') as f:
		rawres = f.read()
	allres = []
	rawres = rawres.split('\n')
	for line in rawres:
		if len(line)==0:
			continue
		line = line.split(' ')
		allres.append( ( float(line[0]) , float(line[1]) ) )
	allres.sort(key=lambda res: res[0] )
	
	# try to fix holes
	max_interval = 1.0
	max_num = 24.9
	missing = []
	prev = 0.0
	if allres[-1][0] < max_num: # fix the end
		allres.append( ( max_num, 0.0 ) )
	for res in allres:
		if res[0]-prev > max_interval :
			# float range
			for i in [ prev+max_interval+f*max_interval for f in range( int(( res[0] - prev) / max_interval)) ]:
				missing.append( ( float(i), 0.0 ) )
		prev = res[0]
	
	allres.extend(missing)
	allres.sort(key=lambda res: res[0] )
	return allres

def parse_iperf(file):
	max_interval = 1.0
	rawres = ''
	with open(file, 'r') as f:
		rawres = f.read()
	allres = re.findall( r'\[\s*\d\]\s*([\d.]*)-\s*([\d.]*)\s*sec\s*[\d.]*\s*\w*\s*([\d.]*)\s*(\w*?)/sec' , rawres )
	
	normres = []
	for res in allres:
		if float(res[1]) - float(res[0]) < max_interval: # don't include the summary at the end
			multiplier = {
				'bits': 1,
				'Kbits': 1024,
				'Mbits': 1024*1024,
				'Gbits': 1024*1024*1024
			}[ res[3] ]
			normres.append( ( float(res[1]), float(res[2]) * multiplier) )
	
	normres.sort(key=lambda res: res[0] )
	return normres

def run_test():
	os.system('mn -c') # cleanup (to empty node's memories)
	# run bandwith test
	os.system('python mptcp_test.py')
	
	time.sleep(3) # wait for logs to close (don't ask why)

def save_logs(file_name_prefix):
	
	csv = parse_iperf('iperf_bandwith_server_log.txt')
	with open('results/'+file_name_prefix+'_bandwith_server_log.csv', 'w') as f:
		for row in csv:
			f.write(str(row[0])+' '+str(row[1])+'\n')
	
	csv = parse_iperf('iperf_bandwith_client_log.txt')
	with open('results/'+file_name_prefix+'_bandwith_client_log.csv', 'w') as f:
		for row in csv:
			f.write(str(row[0])+' '+str(row[1])+'\n')
	
	os.system('cp iperf_bandwith_server_log.txt results/'+file_name_prefix+'_bandwith_server_log.txt');
	os.system('rm iperf_bandwith_server_log.txt');
	
	os.system('cp iperf_bandwith_client_log.txt results/'+file_name_prefix+'_bandwith_client_log.txt');
	os.system('rm iperf_bandwith_client_log.txt');

def create_plot(file_name_prefix, cc, pm, sc):
	
	server_bandwidth = parse_csv('results/'+file_name_prefix+'_bandwith_server_log.csv')
	
	# find out the plot's title
	title = 'congestion-control: '+cc+', path-manager: '+pm+', scheduler: '+sc+''
	print 'create plot:', file_name_prefix, title
	
	layout = plotly.graph_objs.Layout(title=title, yaxis = dict(title='bandwith',showgrid=False) )
	
	data = [
		{
			"x": [float(i[0]) for i in server_bandwidth],	# times
			"y": [float(i[1]) for i in server_bandwidth],	# values
			"name": "server bandwidth",
		}
	]
	fig = plotly.graph_objs.Figure(data=data, layout=layout)
	plotly.plotly.image.save_as(fig, filename= 'results/'+file_name_prefix+'.png')

for cc in [('','cubic'), ('mptcp_coupled','lia'), ('mptcp_olia','olia'), ('mptcp_wvegas','wvegas'), ('mptcp_balia','balia')]:
	if debug and cc[1]!='olia': continue
	if cc[0]:
		os.system('modprobe '+cc[0])
	os.system('sysctl -w net.ipv4.tcp_congestion_control='+cc[1])
	
	for pm in [('','default'), ('','fullmesh'), ('mptcp_ndiffports','ndiffports'), ('mptcp_binder','binder')]:
		if debug and pm[1]!='fullmesh': continue
		if pm[0]:
			os.system('modprobe '+pm[0])
		os.system('sysctl -w net.mptcp.mptcp_path_manager='+pm[1])
		
		for sc in [('','default'), ('mptcp_rr','roundrobin'), ('mptcp_redundant','redundant')]:
			if debug and sc[1]!='default': continue
			if sc[0]:
				os.system('modprobe '+sc[0])
			os.system('sysctl -w net.mptcp.mptcp_scheduler='+sc[1])
			
			file_name_prefix = cc[1]+'_'+pm[1]+'_'+sc[1]
			
			print '\n\nstarting:', cc[1],pm[1],sc[1],'\n\n'
			sys.stdout.flush()	# flush the buffer, unless this, the os.system results will be printed before the regular prints
			
			run_test()
			
			save_logs(file_name_prefix)
			
			if os.path.exists('results/'+file_name_prefix+'.png'):	# in case the plotter failed at a point, and have to re-run the script, avoid recreate existing plots, 
				print 'plot image already exists, skipping'			# since the total generation is limited for one day (max 100 plots)
			else:
				create_plot(file_name_prefix, cc[1], pm[1], sc[1])
			
			print 'one fully ended'

def generate_html():
	f = open('all_images.html','w')
	f.write('<html><body style="width:5000px;"><style>img{width:350px;height:250px;}</style>')
	for cc in [('','cubic'), ('mptcp_coupled','lia'), ('mptcp_olia','olia'), ('mptcp_wvegas','wvegas'), ('mptcp_balia','balia')]:
		for pm in [('','default'), ('','fullmesh'), ('mptcp_ndiffports','ndiffports'), ('mptcp_binder','binder')]:
			for sc in [('','default'), ('mptcp_rr','roundrobin'), ('mptcp_redundant','redundant')]:
				
				file_name_prefix = cc[1]+'_'+pm[1]+'_'+sc[1]
				
				f.write('<img src="results/'+file_name_prefix+'.png" />\n')
				
			#f.write('<span style="display:inline-block;height:250px;border-left: 2px solid black;"></span>\n')
		f.write('<hr>\n')
	f.write('</body></html>')
	f.close()

if not debug:
	generate_html()
