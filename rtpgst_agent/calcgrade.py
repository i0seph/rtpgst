def getgrade(duration):
        if duration < 1250:
                return duration / 50;
        elif duration < 6050:
                return ((duration - 1250) / 200) + 25;
        else:
                return 49;

if __name__ == '__main__':
        for i in xrange(8000):
                print i, getgrade(i);
