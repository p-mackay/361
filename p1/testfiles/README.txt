USAGE: python3 marker.py /path/to/sws.py

This marking script must be run on picolab
(preferrably in the piconet terminal). There
are 12 tests. 1 test worth zero marks that
starts the server, 9 "positive" tests (you
earn marks if you pass them), and 2
"negative" tests (you lose marks if you fail
them). If the output given by your server is
exactly correct, you will get the marks for
each test automatically. If there is some
deviation, the expected and received results
are printed to the console (this is where
the marker decided if the output is correct
or not).

The script will save all output to output.txt.
