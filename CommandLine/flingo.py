#!/usr/bin/env python

# Copyright(c) 2010. Free Stream Media Corp. Released under the terms
# of the GNU General Public License version 2.0.
#
# Author: David Harrison

import os
import httplib
from random import randint
import socket
from urlparse import urlparse
from urllib import quote

# SimpleHTTPServer does not support range requests, which causes fling
# to not operate on many TVs.  twisted does support range requests.
#import SimpleHTTPServer
import SocketServer

# twisted has some external dependencies (Blah) but it supports range
# requests.
from twisted.internet import reactor
from twisted.web.server import Site
from twisted.web.static import File

# In OS X, the following doesn't work as desired:
#   dname, temp, ips = socket.gethostbyname_ex(socket.gethostname())
# ips contains the array ["127.0.0.1"] rather than a list of 
# interfaces on this device.  To solve this problem I use netifaces.
try:
    from netifaces import interfaces, ifaddresses
    found_netifaces = True
except ImportError,e:
    print "WARNING! Failed to import netifaces.  You can obtain netifaces on Windows "
    print "and OSX by running:"
    print "  easy_install netifaces"
    print "Using the less reliable socket.gethostbyname to determine ip address."
    found_netifaces = False



# default port.
PORT = 18761

#image_ext = [ ".png", ".jpeg", ".jpg", ".gif" ]

def get_local_ips():
   """Returns the set of known local IP addresses excluding the loopback 
      interface."""
   global found_netifaces
   ips = []
   if found_netifaces:
       ifs = [ifaddresses(i).get(socket.AF_INET,None) for i in interfaces()]
       ifs = [i for i in ifs if i]
       ips = []
       for i in ifs:
         ips.extend([j.get('addr',None) for j in i])
       ips = [i for i in ips if i and i != "127.0.0.1"]
   if not found_netifaces or not ips:
       ip = socket.gethostbyname(socket.gethostname())
       if ip != "127.0.0.1":
           ips.append(ip)
   return ips


# If no title then the filename is used as the title.
# If no description then a description is generated that states
# where the file came from.  Even if a description is provided,
# where the file came from is appended to the description.
#
def fling( path, port=PORT, title=None, description=None, front=True ):
    if type(port) == str:
        port = int(port)
    print "fling %s from port %d with title %s" % (path, port, title)
    if os.path.isabs(path):
        print "Use relative paths.  %s is absolute" % path
        reactor.stop()
  
    p, ext = os.path.splitext( path )
    d, fname = os.path.split(p)
    if not d:
        d = os.getcwd()
  
    dname = socket.gethostname()
    ips = get_local_ips()
    ip = ips[0]  # HEREDAVE: need to be smarter.
  
    if not title:
        title = fname
  
    if dname and dname != "localhost":
        flung_across_lan = "Flung across local network from machine %s" % (
            "with name %s at ip address %s." % ( dname, ip ))
    else:
        flung_across_lan = "Flung across local network from machine %s " % (
            "with ip address %s." % ip)
  
    if not description: 
        description = ""
    description += flung_across_lan
  
    url = "http://%s:%d/%s" % ( ip, port, path )
  
    print "title:",title
    print "description:", description
    print "url:", url
  
    fling_url = "http://flingo.tv/fling/fling?%s" % (  
        "title=%s&description=%s&url=%s&version=%s&front=%s"%(
        quote(title), quote(description), quote(url), "1.0.12", front ))
  
    print "fling_url:", fling_url
    result = get(fling_url)
  
    print "result:", result


# pulls down resource from given URL and returns the response body as a string.
def get(url):
    (scheme, netloc, path, pars, query, fragment) = urlparse(url)
    lst = netloc.split(":")
    if len(lst) == 2:
        host, port = lst
    else:
        host, port = lst[0], 80
    
    conn = httplib.HTTPConnection(netloc, port)
    
    # http://foo.com/a/b/c?do=blah&po=fa --> /foo.com/a/b/c?do=blah&po=fa
    long_path = "/" + "/".join(url.split("/")[3:])
    conn.request("GET", long_path )
    
    r = conn.getresponse()
    if r.status != 200:
        raise Exception("** fling encountered error. returned status: %s %s"%(
            r.status, r.reason ))
    data = r.read()
    return data


if __name__ == "__main__":
    from optparse import OptionParser
    try:

        usage = """usage: %prog [options] FILE\nThe file is sent (i.e., 
private broadcast to all fling-enabled devices (TVs, bluray) in your local
network.  To find the flung item, start your device and go to the fling-enabled
app (called "Web Videos" on Vizio VIA TVs).  The item should appear at the front of your queue.
    """
    
        parser = OptionParser(usage=usage)
        parser.add_option("-d", "--description", dest="description",
                          help="description of the file to be flung.", 
                          default="" )
        parser.add_option("-t", "--title", dest="title",
                          help="title of the file to be flung.", default="")
        parser.add_option("-p", "--port", dest="port",
                          help= ( "port number from which to serve flung "
                                  "files. By default it uses a random port."),
                          default=-1)
        parser.add_option("-b", "--back", dest="front", action="store_false",
                          help="push to the back of the queue.", default=True )
        
        (options, args) = parser.parse_args()
    
        if len(args) > 1:
            parse.print_usage()
            sys.exit(-1)
    
        fname = args[0]
        if os.path.isabs(fname):
            path, fname = os.path.split(fname)
            os.chdir(path)
        if type(options.port) in [str,unicode]:
            options.port = int(options.port)
        port = options.port
        if port == -1:
            port = 18761 + randint(0,4000)
        fling( fname, port, options.title, options.description,
            front = options.front )
    
        root_dir = os.getcwd()
    
        doc_root = File(root_dir)
        site = Site(doc_root)
        reactor.listenTCP(port, site)
        reactor.run()
    
    except KeyboardInterrupt:
        print '\nCTRL-C received, shutting down'

