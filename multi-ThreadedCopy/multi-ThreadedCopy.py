from threading import Thread
import time

f = open("log.txt","w")
TERM = 10 * 1024

def copy_file(fsrc, fdst, start_time):
    src = open(fsrc, "rb")
    dst = open(fdst, "wb")
    f.write("%.2f\tStart copying %s to %s\n" % ((time.time() - start_time), fsrc, fdst))
    while True :
        tmp_buf = src.read(TERM)
        if not tmp_buf:
            break
        dst.write(tmp_buf)
    f.write("%.2f\t%s is copied completly\n" % ((time.time() - start_time), fdst))
    src.close()
    dst.close()

if __name__ == "__main__" :
    start_time = time.time()
    fsrc = ""
    fdst = ""
    th = list()
    i = 0
    while True:
        fsrc = input("Input the file name :")
        if fsrc == "exit":
            break
        fdst = input("Input the new name :")
        if fdst == "exit":
            break
        th.append(Thread(target=copy_file, args=(fsrc,fdst,start_time)))
        th[i].start()
        i += 1

    j = 0
    while j < i :
        th[j].join()
        j += 1

    f.close()
