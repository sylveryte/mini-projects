#!/bin/bash

#configuration
#set path for dir to create and update index.html and style.css
#use proper path ending with / 

path=/home/sylveryte/public_html/report/

#code init file checkings
_index=index.html
_style=style.css
indexfile=$path$_index
stylefile=$path$_style

#CSS CODE HANDLE
#if css exists and has code
if [ -s "$stylefile" ]; then
	author=sylveryte
else
	touch $stylefile
	tee $stylefile << _EOFC_
body{
  background-color: black;
}
.body{
  background-color: #282828;
  color: white;
  margin: 0% 15%;
  padding: 5px 30px;
  border-radius: 5px;
}
h1,h2,h3{
  background-color:grey;
  border-radius: 10px;
  padding: 10px;
}
.container{
  background-color:#323232;
  padding:25px;
  border-radius: 5px;
  margin: 10px;
}
article,pre{
  color: #d3d3d3;
  padding-left: 20px;
  /*background-color: #484848;*/
  background-color: #282828;
  margin: 5px 0px 0px 15px;
  padding: 20px;
  border-radius: 10px;
}
.pback{
  background-color: #447f61;
  border-radius: 5px;
}
.pfore{
  background-color: #874343;
  padding: 2px;
  border-radius: 5px;
}

_EOFC_
fi

#code

title="System Report of <strong>$HOSTNAME</strong>"
current_time=$(date +"%x %r %Z")
timestamp="Generated on <strong>$current_time</strong> by <strong>$USER</strong>"

report_uptime(){
	cat <<- _EOF_
	<h3>
	Uptime	
	</h3>
	<pre>
	$(uptime)
	</pre>
	_EOF_
	return
}

report_ram_space(){
	echo "<h3>Memory Info</h3><article>"

	
	total=$(free | grep -i mem | awk '{print $2}')
	used=$(free | grep -i mem | awk '{print $3}')
	per=$((100*$used/$total))%


	while read line; do
		echo "<div style=\"padding:7px 0px\">"
		echo "<strong>"
		echo  $line | awk '{print $1}'
		echo "</strong><br>total<strong>:"
		echo  $line | awk '{print $2}'
		echo "</strong><br>available<strong>:"
		echo  $line | awk '{print $4}'
		echo "</strong><br>used<strong>:"
		echo  $line | awk '{print $3}'
		echo "</strong><div style=\"margin:10px 3px\"><div class=\"pback\"><div class=\"pfore\" style=\"width:$per\">$per</div></div></div>"
		echo "</div>"
	done < <(free -h | grep -i mem)
	echo "</article>"
}


report_disk_space(){
	echo "<h3>Disk Size Info</h3><article>"
	#read output of df -h line by line
	while read line; do
		echo "<div style=\"padding:7px 0px\">"
		echo "<strong>"
		echo  $line | awk '{print $1}'
		echo "</strong><br>size<strong>:"
		echo  $line | awk '{print $2}'
		echo "</strong><br>available<strong>:"
		echo  $line | awk '{print $4}'
		echo "</strong><br>used<strong>:"
		echo  $line | awk '{print $3}'
		echo "</strong><div style=\"margin:10px 3px\"><div class=\"pback\"><div class=\"pfore\" style=\"width:"
		echo  $line | awk '{print $5}'
		echo "\">"
		echo  $line | awk '{print $5}'
		echo "</div></div></div>"
		echo "</div>"
	done < <(df -h | grep -vi filesystem)
	echo "</article>"
}

report_usb(){
	cat <<- _EOF_
	<h2>
	Connected USB devices
	</h2>

	<pre>
	$(lsusb)
	</pre>
	_EOF_
	return
}
report_pci(){
	echo "<h2>PCI devices</h2>
	<h4>
	Block Devices	
	</h4><pre>"
		while read line; do
			if [[ $line == b* ]]; then
				echo $line
			fi
	done < <(ls -l /dev | grep -vi total )
	echo "</pre>
	<h4>
	Character Devices
	</h4><pre>"
	while read line; do
			if [[ $line == c* ]]; then
				echo $line
			fi
	done < <(ls -l /dev | grep -vi total )
	echo "</pre>"

	return
}
report_users(){
	cat <<- _EOF_
	<h2>
	User login Activities
	</h2>

	<pre>
	$(last -a | head )
	</pre>
	_EOF_
	return
}




tee $indexfile <<- _EOF_
<html>
	<head>
		<title>$title</title>
		<link rel="stylesheet" type="text/css" href="style.css">
	</head>
<body>
<div class="body">
	<h1>$title</h1>
	<div class="container">$timestamp</div>
	<div class="container">
	$(report_uptime)
	$(report_users)
	$(report_ram_space)
	$(report_usb)
	$(report_disk_space)
	$(report_pci)
	</div>	
</div>
</body>
</html>
_EOF_
