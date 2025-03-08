from app.collect.userCheck import Usercheck
import traceback

ucheck = Usercheck()




def collect_data():
    try:
        # ucheck.collect_provider()
        ucheck.collect_domains()
    except:
        traceback.print_exc()