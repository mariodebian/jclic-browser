#!/usr/bin/env python

# Usage: 
#   from spawner import spawner
#   class someObject:
#      def handlermethod_getData(self, sender, pid, group, data):
#        print data
#
#   someobject = someObject()
#
#   spawner.connect("child-data-received", someobject.handlermethod_getData)
#   pid = spawner.spawn("program", "stuff")
#

import os
import signal
import errno
import exceptions
import pygtk
pygtk.require("2.0")
import gtk
import gobject
import popen2
import string
import fcntl
import select

processes = {} # pipe -> group
processesR = {} # group -> pipes
processesHandle = {} # pipe -> input_add handle
processesObj = {} # pipefromchild -> popen4 object
processesPIDToPipe = {} # pid -> pipe

def _realkill_cb(pipe):
	#os.waitpid(pipe.pid, os.WNOHANG)
	pipe.poll()
	return False

# | gobject.SIGNAL_ACTION,
class Spawner(gobject.GObject):

	__gsignals__ = {
		"child-terminated": (
			gobject.SIGNAL_RUN_LAST,
			gobject.TYPE_NONE, 
			(gobject.TYPE_INT,gobject.TYPE_PYOBJECT,gobject.TYPE_INT) # pid,group,exitcode
		),
		"child-data-received": (
			gobject.SIGNAL_RUN_LAST, 
			gobject.TYPE_NONE, 
			(gobject.TYPE_INT,gobject.TYPE_PYOBJECT,gobject.TYPE_STRING) # pid,group,data
		),
		"child-spawned": (
			gobject.SIGNAL_RUN_LAST, 
			gobject.TYPE_NONE, 
			(gobject.TYPE_INT,gobject.TYPE_PYOBJECT) # pid, group
		)
		
	}
	
	def getRealExitCode(exitcode):
		return os.WEXITSTATUS(exitcode)  # without "app not found" stuff etc
		
	def _emit(self, signalName, *args):
		self.emit(signalName, *args)
		pass
		
	def readCb(self, fdd, cond):
		done = False
		try:
			pipe = processesObj[fdd]
			pid = pipe.pid
			group = processes[fdd]
		except:
			return True
			
		try:
			res = select.select([fdd], [], [], 10)
			data = ""
			while fdd in res[0]:
				b = fdd.read(1024)
				if b == "":
					done = True
					break
				else:
					data = data + b
					
				if data != "":
					self._emit("child-data-received", pid, group, data)
					data = ""

		except exceptions.IOError, e:
			if e.errno == errno.EAGAIN: # normal error
				pass
			else: # bad error
				done = True
			pass
				
		except exceptions.Exception, e:
			print type(e)
			print e
			done = True
			pass
			
		return done

	def _kick(self, fdd):
		exitcode = 0
		pid = 0
		group = None
		try:
			pipe = processesObj[fdd]
			pid = pipe.pid
			i = pipe.poll() 
			if i != -1:
				# terminated
				exitcode = i
		except:
			pass

		if pid in processesPIDToPipe:
			del processesPIDToPipe[pid]
			
		group = processes[fdd]
		del processes[fdd]
		arr = processesR[group]
		if fdd in arr: arr.remove(fdd)
		try:
			del processesHandle[fdd]
		except:
			pass

		try:
			del processesObj[fdd]
		except:
			pass

		return pid, group, exitcode
	
	def cb(self, fdd, cond):
		#if cond & gtk.gdk.INPUT_EXCEPTION:
		#    pass
		global processesObj
		global processesHandle
		global processesR
		global processes
		global processesPIDToPipe
		
		done = False
		if cond & gtk.gdk.INPUT_READ:
			done = self.readCb(fdd, cond)

		if done == True: # cond == 16: # hack
			#return False

			#if (cond & gtk.gdk.INPUT_READ) != 0:
			#fdd.read()

			#if (cond & gtk.gdk.INPUT_EXCEPTION) != 0:
			
			try:
				pid, group, exitcode = self._kick(fdd)
			except:
				pass			

			self._emit("child-terminated", pid, group, exitcode)

			return False

		return True

	def spawn(self, cmd, group):
		global processes
		global processesHandle
		global processesR
		global processesObj
		global processesPIDToPipe
		#a = string.split(cmd, " ")
		#if len(a) > 0:
		if type(cmd) != basestring or cmd != "":
			# handle "command not found" immediately ? nope.
			
			# x = popen2.popen4
			# return_code = os.WEXITSTATUS(x.close())
			
			pipe = popen2.Popen4(cmd)
			fc = pipe.fromchild
			#(fin, fc, ferr) = os.popen3(cmd)

			fno = fc.fileno()
			flags = fcntl.fcntl (fno, fcntl.F_GETFL, 0)
			flags = flags  | os.O_NONBLOCK
			fcntl.fcntl (fno, fcntl.F_SETFL, flags)

			#pid = os.spawnlp(os.P_NOWAIT, a[0], a)
			processesObj[fc] = pipe
			processes[fc] = group
			if not (group in processesR):
				processesR[group] = []

			processesPIDToPipe[pipe.pid] = pipe

			processesR[group].append(fc)
			self._emit("child-spawned", pipe.pid, group)

			processesHandle[fc] = gtk.input_add(fc, gtk.gdk.INPUT_READ | gtk.gdk.INPUT_EXCEPTION, 
self.cb)
			return pipe.pid

		return None
					
	def count(self, group):
		global processesR
		try:
			return len(processesR[group])
		except:
			return 0

	def poll(self):
		global processes
		pass
		#for k,v  in processes.items():
		#	k.poll()
		
	def kill(self, pid, signal = signal.SIGINT):
		global processesPIDToPipe
		
		try:
			pipe = processesPIDToPipe[pid]
			self._kick(pipe.fromchild)
			pipe.fromchild.close() # close end to make it break on sigpipe :->
			pipe.tochild.close()
			pipe.poll()
		except:
			pass

		os.kill(pid, signal)
		gtk.timeout_add(2000, _realkill_cb, pipe)

gobject.type_register(Spawner)
		
spawner = Spawner()

if __name__ == "__main__":
	# awfully long but async way of doing "ls":
	
	class someObject:
		def __init__(self):
			spawner.connect("child-data-received", self.handlermethod_getData)
		
		def handlermethod_getData(self, sender, pid, group, data):
			print "pid", pid
			print "group", group
			print "data", data

	someobject = someObject()
	
	pid = spawner.spawn("/bin/bash -c ls", "stuff")
	spawner.connect("child-terminated", gtk.main_quit)
	print pid

	gtk.main()
