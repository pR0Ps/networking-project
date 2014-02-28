TCP Socket Programming
======================

For a CISC 435 Computer Networks project

Assignment Instructions
-----------------------
1. Install and run any TCP client and server programs on the same host machine
2. Modify the client and server programs such that you can:
  1. Create n TCP servers, where n is an input. Verify that n is at least 2.
  2. Assign a virtual host name for each server, e.g. S1, S2, etc.
  3. Have each TCP server generate a random number between 1 and 10 at startup.
  4. Create an additional server that will act as the central tracker for other servers.
  5. Have all n server connect to the central server, sending it a “Hello” message.
  6. Create n TCP clients and assign a virtual host name for each Client, e.g. C1, C2,
     etc. Have all TCP clients connect to the central tracker and send “Hi” message.
  7. Every TCP client will send a request that consists of the client’s host name and a
     random number between 1 and 10 to the central tracker. The central tracker will
     forward the request to all connected TCP servers.
  8. Only TCP servers with a generated number that matches the one in the request
     will reply back to the central tracker within a time limit of 2 seconds. The central
     tracker will forward the host names of replied TCP servers to the corresponding
     requester TCP client. In case there are no matching TCP servers, the central
     tracker will reply with “No match has been found”.
  9. Repeat the steps g and h five times.
  10. Your program must print the status and content of every message sent and
      received, e.g. for 3 peers:
         
          S1: sending “Hello” to Central.
          S1: selected random number is 3.
          Central: received “Hello” from Sever S1.
          S2: sending “Hello” to Central.
          S2: selected random number is 7.
          Central: received “Hello” from Server S2.
          S3: sending “Hello” to Central.
          S3: selected random number is 3.
          Central: received “Hello” from Server S3.
          C1: sending “Hi” to Central.
          Central: received “Hi” from Client C1.
          C2: sending “Hi” to Central.
          Central: received “Hi” from Client C2.
          C3: sending “Hi” to Central.
          Central: received “Hi” from Client C3.
          C1: find match of 5
          Central: process match request from C1
          Central: send match reply to C1
          C1: No match has been found
          C2: find match of 3
          Central: process match request from C2
          Central: send match reply to C2
          C2: Match found on servers S1 and SS
          ...

Running
-------

Just run `./project.py` to run the assignment. Requires Python 3.
