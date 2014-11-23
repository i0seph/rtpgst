import time,threading

class timer(threading.Thread):
        def __init__(self, interval):
                self.interval = interval;
                self.next_timestamp = int(time.time()) + interval - (time.localtime(time.time())[5] % interval);
                threading.Thread.__init__(self);
        def run(self):
                while 1:
                        if self.next_timestamp == int(time.time()):
                                self.next_timestamp += self.interval;
                        time.sleep(0.01);


if __name__ == '__main__':
	t = timer(1);
	t.daemon = True;
	t.start();
	while 1:
		print t.next_timestamp;
		time.sleep(0.1);
