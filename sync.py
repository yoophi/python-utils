import logging
import os
import time

import paramiko
from scp import SCPClient
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

HOME_DIR = os.path.expanduser("~")
watch_dir = os.environ.get('WATCH_DIR')
file_pattern = os.environ.get('WATCH_PATTERN')
dest_dir = os.environ.get('DEST_DIR')
host_name = os.environ.get('HOST_NAME')
host_port = os.environ.get('HOST_PORT')
username = os.environ.get('USERNAME')


def scp_file(filename):
    source_file = os.path.join(watch_dir, filename)
    dest_file = os.path.join(dest_dir, filename)

    private_key = paramiko.RSAKey.from_private_key_file(os.path.join(HOME_DIR, ".ssh/id_rsa"))

    ssh = paramiko.SSHClient()
    ssh.load_system_host_keys()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=host_name, username=username, pkey=private_key, port=host_port)

    scp = SCPClient(ssh.get_transport())

    try:
        logging.debug(f'scp.put - {filename}')
        scp.put(source_file, dest_file)
        logging.debug(f'scp.put completed - {filename}')

        return True
    except Exception:
        logging.exception('exception')
        return False


class MyHandler(FileSystemEventHandler):

    def on_modified(self, event):
        logging.info('on_modified >>>')
        for filename in os.listdir(watch_dir):
            if file_pattern in filename:
                logging.info(f'uploading {filename}')
                res = scp_file(filename)
                if res:
                    logging.info(f'deleting {filename}')
                    os.unlink(os.path.join(watch_dir, filename))

        logging.info('on_modified <<<')


if __name__ == '__main__':

    event_handler = MyHandler()
    observer = Observer()
    observer.schedule(event_handler, watch_dir, recursive=True)
    observer.start()

    logging.info(f"WATCH_DIR: {watch_dir}")
    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        logging.info("KeyboardInterrupt")
        observer.stop()

    observer.join()
