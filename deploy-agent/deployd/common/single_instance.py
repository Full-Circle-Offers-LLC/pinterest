from __future__ import print_function
from __future__ import absolute_import
# Copyright 2016 Pinterest, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import os
import stat
import errno
import fcntl
from . import utils
from future.utils import PY3

log = logging.getLogger(__name__)
LOCKFILE_DIR = '/var/lock'


class SingleInstance(object):
    def __init__(self):
        # Establish lock file settings
        appname = 'deploy-agent'
        lockfile_name = '.{}.lock'.format(appname)
        self._create_lock_dir()
        lockfile_path = os.path.join(LOCKFILE_DIR, lockfile_name)
        lockfile_flags = os.O_WRONLY | os.O_CREAT
        # This is 0o222, i.e. 146, --w--w--w-
        lockfile_mode = stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH

        # Create lock file
        umask_original = os.umask(0)
        try:
            lockfile_fd = os.open(lockfile_path, lockfile_flags, lockfile_mode)
        finally:
            os.umask(umask_original)

        # Try locking the file
        try:
            fcntl.lockf(lockfile_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except IOError:
            print(('Error: {0} may already be running. Only one instance of it '
                   'can run at a time.').format(appname))
            # noinspection PyTypeChecker
            os.close(lockfile_fd)
            utils.exit_abruptly(1)

    def _create_lock_dir(self):
        if PY3:
            os.makedirs(LOCKFILE_DIR, exist_ok=True)
        else:
            # Need to handle the case when lock dir exists in py2
            try:
                os.makedirs(LOCKFILE_DIR)  # py2
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise
