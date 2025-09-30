import threading
import time

# Shared state
shared_data = {"value1": None, "value2": None}
lock = threading.Lock()
condition = threading.Condition(lock)

def worker(name, key, other_key):
    for i in range(5):
        with condition:
            # Update my value
            shared_data[key] = f"{name} -> {i}"
            print(f"[{name}] set {key} = {shared_data[key]}")

            # Signal the other thread
            condition.notify_all()

            # Wait until the other has updated theirs
            while shared_data[other_key] is None or shared_data[other_key].endswith(str(i)):
                condition.wait()

            print(f"[{name}] sees {other_key} = {shared_data[other_key]}")

        time.sleep(0.5)

# Start two threads with different inputs
t1 = threading.Thread(target=worker, args=("Thread-1", "value1", "value2"))
t2 = threading.Thread(target=worker, args=("Thread-2", "value2", "value1"))

t1.start()
t2.start()
t1.join()
t2.join()
