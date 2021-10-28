from multiprocessing import Process, Value, Pool, Array, Queue
import traceback
from functools import partial
from ctypes import c_wchar_p, c_char_p
from typing import List


def test(index: int, queue: Queue):
    ret = queue.get()
    ret[index] = "Test %s" % index
    queue.put(ret)
    # print("Process", i, queue.get())


if __name__ == "__main__":
    count = 20
    q = Queue()
    q.put({index: False for index in range(count)})
    processes: List[Process] = []
    for i in range(count):
        p = Process(target=test, args=(i, q))
        processes.append(p)
        p.start()
    for p in processes:
        p.join()

    print("Queue:", q.get())
