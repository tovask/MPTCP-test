#!/usr/bin/python
import os
import sys
import time
import subprocess
import re
import plotly # https://plot.ly/python/reference/#scatter


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

def parse_log(file):
	rawres = ''
	with open(file, 'r') as f:
		rawres = f.read()
	allres = re.findall( r'([\d.]+)\ss\s*\|\s*([\d.]+)\sbit/s\s\|\s*([\d.A-Za-z]+)\ss\s\|\s*([\d.-A-Za-z]+)\ss' , rawres )
	allres.sort(key=lambda res: float(res[0]) )
	
	# try to fix holes
	max_interval = 1.0
	max_num = 59.0
	missing = []
	prev = 0
	if float(allres[-1][0]) < max_num: # fix the end
		allres.append( (str(max_num), '0.00', 'inf', 'inf') )
	for res in allres:
		if float(res[0])-prev > max_interval :
			# float range
			for i in [ prev+max_interval+f*max_interval for f in range( int((float(res[0]) - prev) / max_interval)) ]:
				missing.append( (str(i), '0.00', 'inf', 'inf') )
		prev = float(res[0])
	
	allres.extend(missing)
	allres.sort(key=lambda res: float(res[0]) )
	return allres

def get_column(data,n):
	return [float(i[n]) if i[n]!='inf' else None for i in data]

def run_test():
	#os.system('mn -c') # cleanup (to empty node's memories)
	# run latency test
	#os.system('python mptcp_test.py latency')
	
	os.system('mn -c') # cleanup (to empty node's memories)
	# run bandwith test
	os.system('python mptcp_test.py')
	
	time.sleep(3) # wait for logs to close (don't ask why)

def save_logs(file_name_prefix):
	# file_name_prefix = 'mininet_10s'
	# file_name_prefix = 'mininet_600s'
	# file_name_prefix = 'mininet_rnd1'
	# file_name_prefix = 'mininet_rnd2'
	# file_name_prefix = 'mininet_rnd3'
	# file_name_prefix = 'mininet_rnd4'
	
	# os.system('cp latency_client_log.txt results/'+file_name_prefix+'_latency_client_log.txt');
	# os.system('cp latency_server_log.txt results/'+file_name_prefix+'_latency_server_log.txt');
	# os.system('cp bandwith_client_log.txt results/'+file_name_prefix+'_bandwith_client_log.txt');
	# os.system('cp bandwith_server_log.txt results/'+file_name_prefix+'_bandwith_server_log.txt');
	
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
	#file_name_prefix = 'mininet_10s'
	#file_name_prefix = 'mininet_600s'
	#file_name_prefix = 'mininet_rnd1'
	#file_name_prefix = 'mininet_rnd2'
	#file_name_prefix = 'mininet_rnd3'
	#file_name_prefix = 'mininet_rnd4'
	
	# get the data
	#client_lat = parse_log('results/'+file_name_prefix+'_latency_client_log.txt') #if (not debug) else parse_log('latency_client_log.txt')
	#server_lat = parse_log('results/'+file_name_prefix+'_latency_server_log.txt') #if (not debug) else parse_log('latency_server_log.txt')
	#client_ban = parse_log('results/'+file_name_prefix+'_bandwith_client_log.txt') #if (not debug) else parse_log('bandwith_client_log.txt')
	#server_ban = parse_log('results/'+file_name_prefix+'_bandwith_server_log.txt') #if (not debug) else parse_log('bandwith_server_log.txt')
	
	server_ban = parse_csv('results.4/'+file_name_prefix+'_1_bandwith_server_log.csv')
	
	# find out the plot's title
	title = 'congestion-control: '+cc+', path-manager: '+pm+', scheduler: '+sc+''
	print 'create plot:', file_name_prefix, title
	
	#layout = plotly.graph_objs.Layout(title=title, yaxis = dict(title='bandwith',showgrid=False), yaxis2=dict(title='delay',overlaying='y',side='right',showgrid=False) )
	layout = plotly.graph_objs.Layout(title=title, yaxis = dict(title='bandwith',showgrid=False) )
	
	#"type": "scatter",
	#"mode": "lines",
	#"line": {"shape": "spline"},
	data = [
		# {
		# 	"x": get_column(client_ban, 0),
		# 	"y": get_column(client_ban, 1),
		# 	"name": "client bandwidth",
		# },
		{
			"x": get_column(server_ban, 0),
			"y": get_column(server_ban, 1),
			"name": "server bandwidth",
		},
		# {
		# 	"x": get_column(client_lat, 0),
		# 	"y": get_column(client_lat, 2),
		# 	"name": "client delay1",
		# 	"yaxis": "y2",
		# },
		# {
		# 	"x": get_column(client_lat, 0),
		# 	"y": get_column(client_lat, 3),
		# 	"name": "client delay2",
		# 	"yaxis": "y2",
		# },
		# {
		# 	"x": get_column(server_lat, 0),
		# 	"y": get_column(server_lat, 2),
		# 	"name": "server delay1",
		# 	"yaxis": "y2",
		# },
		# {
		# 	"x": get_column(server_lat, 0),
		# 	"y": get_column(server_lat, 3),
		# 	"name": "server delay2",
		# 	"yaxis": "y2",
		# }
	]
	fig = plotly.graph_objs.Figure(data=data, layout=layout)
	#plot_url = plotly.plotly.plot(fig, filename = file_name_prefix, auto_open=False)
	#print plot_url
	#with open('results/'+file_name_prefix+'_link.txt', 'w') as f:
	#	f.write(plot_url)
	plotly.plotly.image.save_as(fig, filename= 'results/'+file_name_prefix+'.png')


#sysctl net.mptcp
#sysctl net | grep congestion
#sysctl net | grep 'mptcp\|congestion'

"congestion controls:"
#os.system('sysctl -w net.ipv4.tcp_congestion_control=cubic ')
#os.system('modprobe mptcp_coupled && sysctl -w net.ipv4.tcp_congestion_control=lia ')
#os.system('modprobe mptcp_olia && sysctl -w net.ipv4.tcp_congestion_control=olia ')
#os.system('modprobe mptcp_wvegas && sysctl -w net.ipv4.tcp_congestion_control=wvegas ')
#os.system('modprobe mptcp_balia && sysctl -w net.ipv4.tcp_congestion_control=balia ')

"path-managers:"
#os.system('sysctl -w net.mptcp.mptcp_path_manager=default ')
#os.system('sysctl -w net.mptcp.mptcp_path_manager=fullmesh ')
#os.system('echo 1 | sudo tee /sys/module/mptcp_fullmesh/parameters/num_subflows')
#os.system('modprobe mptcp_ndiffports && sysctl -w net.mptcp.mptcp_path_manager=ndiffports ')
#os.system('echo 1 | sudo tee /sys/module/mptcp_ndiffports/parameters/num_subflows')
#os.system('modprobe mptcp_binder && sysctl -w net.mptcp.mptcp_path_manager=binder ')

"scheduler:"
#os.system('sysctl -w net.mptcp.mptcp_scheduler=default ')
#os.system('modprobe mptcp_rr && sysctl -w net.mptcp.mptcp_scheduler=roundrobin ')
#os.system('echo 1 | sudo tee /sys/module/mptcp_rr/parameters/num_segments')
#os.system('echo Y | sudo tee /sys/module/mptcp_rr/parameters/cwnd_limited')
#os.system('modprobe mptcp_redundant && sysctl -w net.mptcp.mptcp_scheduler=redundant ')


for sequence in [1,2,3,4,5]:
	if debug and sequence!=1: continue
	if True and sequence!=1: continue
	
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
				sys.stdout.flush()
				
				#run_test()
				
				#save_logs(file_name_prefix + "_"+str(sequence) )
				
				if os.path.exists('results/'+file_name_prefix+'.png'):
					print 'already exists, skipping'
					continue
				
				create_plot(file_name_prefix, cc[1], pm[1], sc[1])
				
				print 'one full ended'

def generate_html():
	f = open('sc-def.html','w')
	f.write('<html><body style="width:5000px;"><style>img{width:350px;height:250px;}</style>')
	for cc in [('','cubic'), ('mptcp_coupled','lia'), ('mptcp_olia','olia'), ('mptcp_wvegas','wvegas'), ('mptcp_balia','balia')]:
		for pm in [('','default'), ('','fullmesh'), ('mptcp_ndiffports','ndiffports'), ('mptcp_binder','binder')]:
			for sc in [('','default'), ('mptcp_rr','roundrobin'), ('mptcp_redundant','redundant')]:
				
				if sc[1]!='default': continue
				
				file_name_prefix = cc[1]+'_'+pm[1]+'_'+sc[1]
				
				f.write('<img src="results/'+file_name_prefix+'.png" />\n')
				
				pass
			#f.write('<span style="display:inline-block;height:250px;border-left: 2px solid black;"></span>\n')
		f.write('<hr>\n')
	f.write('</body></html>')
	f.close()

#generate_html()

# find out what we tested
# test_name = ''#'MPTCP: '
# test_name += 'congestion-control: '+re.search( r'=\s*(\w*)', subprocess.Popen("sysctl net.ipv4.tcp_congestion_control", shell=True, stdout=subprocess.PIPE).stdout.read() ).group(1)+', '
# test_name += 'path-manager: '+re.search( r'=\s*(\w*)', subprocess.Popen("sysctl net.mptcp.mptcp_path_manager", shell=True, stdout=subprocess.PIPE).stdout.read() ).group(1)+', '
# test_name += 'scheduler: '+re.search( r'=\s*(\w*)', subprocess.Popen("sysctl net.mptcp.mptcp_scheduler", shell=True, stdout=subprocess.PIPE).stdout.read() ).group(1)
