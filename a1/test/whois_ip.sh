#!/bin/bash

ips=(
"
10.0.0.1
24.68.0.1
64.59.162.113
24.244.62.1
24.244.61.109
66.163.72.22
66.163.68.18
72.14.221.102
8.8.8.8
"
)

for ip in $ips; do
    whois "$ip" | grep -i orgname
done
