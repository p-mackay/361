(a) When testing my code against the test files given in lab 4 I was getting the expected output.
Even though I knew that my code had issues (i.e could not read manually entered requests using nc),
I thought despite its issues it would potentially pass the majority of 
the tests from the marking scripts, this was not the case. My initial submission failed most of the tests. 

(b) Main changes:
- Messages are buffered (line 121) before being read, allowing for manual entry of requests. (following the
    recommendation in the labs)
- Uses OOP making the code much cleaner, and easier to read.
- Got rid of unnecessary regular expressions, when reading a request. Replaced with simpler pattern matching.
- When connection type is "close" it properly closes and does not read requests after that point.
- Using classes made getting logging information much easier. And overall much easier to work with.
The main issue with my initial design was that requests were not being buffered before being enqueued.
This meant that manually entered requests were not possible, and the keep-alive header really didn't
keep the connection alive. It was a very ridged design that only accepted requests in batch files. 

