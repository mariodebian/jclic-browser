import threading

counter=1

class FractionSetter(threading.Thread):
	stopthread = threading.Event()
	
	def run(self):
		global counter
		"""while sentence will continue until the stopthread event is set"""
		while not self.stopthread.isSet():
			print "I'm a fancy thread %d, yay!" %(counter)
			counter=counter+1
	
	def stop(self):
		self.stopthread.set()
		

print counter
fs = FractionSetter()
fs.start()

#Waiting 2 seconds until the thread stop
import time
time.sleep(2)

#Stopping the thread
fs.stop()

