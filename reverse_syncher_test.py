from reverse_syncer import *

def test_listing_device():
    list =adb_manager.list_adb_devices()
    print(list)
def test_reverse_sync():
    devices = adb_manager.list_adb_devices()
    d1 = "" 
    for d in devices:
        d1 = d["serial"]
        break
    print(d1)
    
if __name__ == "__main__":
    # test_listing_device()
    test_reverse_sync()