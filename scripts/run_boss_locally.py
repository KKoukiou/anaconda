#!/usr/bin/python3

import os
import tempfile
import glob
import pydbus
import time
from gi.repository import Gio

from pyanaconda.dbus.constants import DBUS_BOSS_NAME

paths = os.environ.get("PYTHONPATH", "").split(":")
paths.insert(0, os.path.abspath(".."))
os.putenv("PYTHONPATH", ":".join(paths))  # pylint: disable=environment-modify

MODULES_DIR = os.path.abspath("../pyanaconda/modules")
DBUS_SERVICES_DIR = "../data/dbus/"
STARTUP_SCRIPT = os.path.abspath("../scripts/start-module")
EXEC_PATH = 'Exec=/usr/libexec/anaconda/start-module'

print("creating a temporary directory for DBUS service files")
temp_service_dir = tempfile.TemporaryDirectory(prefix="anaconda_dbus_")
print(temp_service_dir.name)

print("copying & modifying DBUS service files")
modified_exec_path = 'Exec={}'.format(STARTUP_SCRIPT)
for file_path in glob.glob(DBUS_SERVICES_DIR +  "*.service"):
    filename = os.path.split(file_path)[1]
    target_file_path = os.path.join(temp_service_dir.name, filename)
    with open(file_path, "rt") as input_file:
        with open(target_file_path, "wt") as output_file:
            for line in input_file:
                # change path to the startup script to point to local copy
                output_file.write(line.replace(EXEC_PATH, modified_exec_path))

test_dbus = Gio.TestDBus()

# set service folder
test_dbus.add_service_dir(temp_service_dir.name)

try:
    # start the custom DBUS daemon
    print("starting custom dbus session")
    test_dbus.up()
    print(test_dbus.get_bus_address())

    # our custom bus is now running, connect to it
    test_dbus_connection = pydbus.connect(test_dbus.get_bus_address())

    print("starting Boss")
    test_dbus_connection.dbus.StartServiceByName(DBUS_BOSS_NAME, 0)

    input("press any key to stop Boss and cleanup")

    print("stopping Boss")

    boss_object = test_dbus_connection.get(DBUS_BOSS_NAME)
    boss_object.Quit()

    print("waiting a bit for module shutdown to happen")
    time.sleep(1)

finally:
    # stop the custom DBUS daemon
    print("stopping custom dbus session")
    test_dbus.down()

# cleanup
print("cleaning up")
temp_service_dir.cleanup()
# done
print("done")