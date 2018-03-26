ni Projects

## OS
	sh script to create html+css system report.
### How to run
1. Read os/report.sh
## NPL 
	distributed sha1 password cracker
### How to run

tip: get sha1 code from [here](http://www.sha1-online.com/)(make sure to use lenght of string 6 or less)

1. from pc1 run master 
	* syntax : `python3 master.py [local ip addr] [port] [sha1 code]`
	* eg     : `python3 master.py 192.168.1.105 9987 e5acb1a96e34cd7f263aada0b69aa58bdd722a03`
1. from pc2..n run slave
	* syntax : `python3 slave.py [master ip addr] [master port]`
	* eg     : `python3 slave.py 192.168.1.105 9987`
