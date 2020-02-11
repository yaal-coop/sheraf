import io
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import warnings

import portpicker
import ZODB.POSException

import sheraf
from sheraf.databases import Database, LocalData


class Conflict(object):
    def __call__(self, times=1):
        if not hasattr(self, "times"):
            self.times = 0
            raise ZODB.POSException.ConflictError()
        else:
            self.times = self.times + 1
            if self.times < times:
                raise ZODB.POSException.ConflictError()

    def reset(self):
        try:
            delattr(self, "times")
        except AttributeError:
            pass


conflict = Conflict()


def create_temp_directory():
    persistent_dir_path = tempfile.mkdtemp()
    _old_files_root_dir = sheraf.attributes.files.FILES_ROOT_DIR
    sheraf.attributes.files.FILES_ROOT_DIR = os.path.join(persistent_dir_path, "files/")
    os.makedirs(sheraf.attributes.files.FILES_ROOT_DIR)
    return persistent_dir_path, _old_files_root_dir


def delete_temp_directory(persistent_dir_path, _old_files_root_dir):
    shutil.rmtree(persistent_dir_path)
    sheraf.attributes.files.FILES_ROOT_DIR = _old_files_root_dir


def create_blob_directory(persistent_dir):
    blob_dir = os.path.join(persistent_dir, "blobs/")
    os.makedirs(blob_dir)
    os.chmod(blob_dir, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
    return blob_dir


def create_database(db_args):
    try:
        return Database(**db_args)
    except KeyError:  # pragma: no cover
        db_name = db_args.get("database_name") or Database.DEFAULT_DATABASE_NAME
        last_context = LocalData.get().last_database_context.get(db_name)
        warnings.warn(
            "Database '{}' was already open on {} at line {}".format(
                db_name, last_context[0], last_context[1]
            )
            if last_context
            else "Database '{}' was already open".format(db_name)
        )
        Database.get(db_name).close()
        return Database(**db_args)


def close_database(database=None):
    if database:
        database.close()

    for db_name, db in list(Database.all()):
        last_context = LocalData.get().last_database_context.get(db.name)
        warnings.warn(
            "Database '{}' was not closed. It should be closed inside the test. It was opened on {} at {}".format(
                db_name, last_context[0], last_context[1]
            )
            if last_context
            else "Database '{}' was not closed. It should be closed inside the test.".format(
                db_name
            )
        )
        db.close()


ZEO_CONFIGURATION_FILE_CONTENT = """
<zeo>
    address localhost:{port}
</zeo>
<filestorage>
    path {path}
    {blob_dir}
</filestorage>
<eventlog>
    level DEBUG
    <logfile>
        path STDOUT
        format %(asctime)s %(levelname)s %(message)s
    </logfile>
</eventlog>
"""


def create_zeo_configuration_file(
    zeo_port, zeo_conf_path, file_storage_path, blob_dir=None
):
    conf_content = ZEO_CONFIGURATION_FILE_CONTENT.format(
        port=zeo_port,
        path=file_storage_path,
        blob_dir="blob-dir {}".format(blob_dir) if blob_dir else "",
    )
    with io.open(zeo_conf_path, "w") as f:
        f.write(conf_content)


def start_zeo_server(persistent_dir, blob_dir=None):
    zeo_port = portpicker.pick_unused_port()
    file_storage_path = os.path.join(persistent_dir, "Data.fs")
    zeo_conf_path = os.path.join(persistent_dir, "zeo.conf")

    create_zeo_configuration_file(zeo_port, zeo_conf_path, file_storage_path, blob_dir)
    zeo_process = subprocess.Popen(
        ("env", "PYTHONPATH=.", "runzeo", "-C", zeo_conf_path),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return zeo_process, zeo_port


def stop_zeo_server(zeo_process, silent=False):
    zeo_process.kill()
    stdout, stderr = zeo_process.communicate()

    if stdout and not silent:
        print("[runzeo STDOUT]")
        sys.stdout.write(stdout.decode())

    if stderr and not silent:  # pragma: no cover
        print("[runzeo STDERR]")
        sys.stdout.write(stderr.decode())


def start_postgresql_server(persistent_dir):
    AFTER_PSQL_SERVER_LAUNCH_SLEEP_TIME = 1
    pg_user = os.getlogin()
    pg_port = portpicker.pick_unused_port()
    pg_dir = os.path.join(persistent_dir, "pgdata")
    try:
        exit_code = subprocess.call(
            ("initdb", "--auth", "trust", "--pgdata", pg_dir, "--username", pg_user),
            stdout=open("/dev/null"),
        )
    except IOError:  # pragma: no cover
        warnings.warn(
            "Postgresql seems to not be installed on this system. Be sure 'initdb' is in your $PATH"
        )
        return None, None, None, "Postgresql seems to not be installed on this system."

    if exit_code == 1:  # pragma: no cover
        return None, None, None, "Postgresql server initialization has failed."

    try:
        pg_process = subprocess.Popen(
            (
                "postgres",
                "-D",
                pg_dir,
                "-p",
                "{}".format(pg_port),
                "-k",
                persistent_dir,
            ),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except IOError:  # pragma: no cover
        warnings.warn(
            "Postgresql seems to not be installed on this system. Be sure 'postgres' is in your $PATH"
        )
        return None, None, None, "Postgresql seems to not be installed on this system."

    time.sleep(AFTER_PSQL_SERVER_LAUNCH_SLEEP_TIME)

    try:
        exit_code = subprocess.call(
            ("createdb", "zodb", "--port", "{}".format(pg_port), "--host", "localhost"),
            stdout=open("/dev/null"),
        )
    except IOError:  # pragma: no cover
        warnings.warn(
            "Postgresql seems to not be installed on this system. Be sure 'createdb' is in your $PATH"
        )
        return None, None, None, "Postgresql seems to not be installed on this system."

    if exit_code == 1:  # pragma: no cover
        return None, None, None, "Postgresql database creation has failed."

    return pg_process, pg_user, pg_port, None


def stop_postgresql_server(pg_process, silent=False):
    pg_process.kill()
    stdout, stderr = pg_process.communicate()

    if stdout and not silent:  # pragma: no cover
        print("[postgresql STDOUT]")
        sys.stdout.write(stdout.decode(errors="ignore"))

    if stderr and not silent:  # pragma: no cover
        print("[postgresql STDERR]")
        sys.stdout.write(stderr.decode(errors="ignore"))
