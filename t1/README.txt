The program in its current state can only read/process requests that are piped in from a file.
Manually entering requests does NOT work. i.e 
$nc sws_ip sws_port 
"some request" <enter> "header" <enter><enter>
Does not work
