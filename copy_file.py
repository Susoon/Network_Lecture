import shutil
import os
from threading import Thread

f = open("log.txt","w")
TERM = 10 * 1024

def copy_file(fsrc, fdst):
    src = open(fsrc, "rb")
    dst = open(fdst, "wb")
    current = 0
    src.seek(0,2)
    end = src.tell()
    src.seek(0)
    f.write(str(current))
    f.write("\t" + "Start copying " + fsrc + " to " + fdst + "\n")
    while(src.tell() != end):
        tmp = src.tell()
        shutil.copyfileobj(src,dst,TERM)
        current += src.tell() - tmp
        f.write(str(current))
        f.write("\t" + "copying " + fsrc +" to " + fdst + "\n")
    f.write(str(current))
    f.write("\t" + fdst + " is copied completly\n")
    src.close()
    src.close()

if __name__ == "__main__" :
    fsrc = ""
    fdst = ""
    th = list()
    i = 0
    while i != 10:
        fsrc = input("Input the file name :")
        if fsrc == "exit":
            break
        fdst = input("Input the new name :")
        th.append(Thread(target=copy_file, args=(fsrc,fdst)))
        th[i].start()
        i += 1

    j = 0
    i -= 1
    while j <= i :
        th[j].join()
        j += 1

