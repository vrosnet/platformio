# Copyright 2014-2016 Ivan Kravets <me@ikravets.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import

from os.path import isfile, join
from shutil import copyfile
from time import sleep
from urlparse import urlparse

import paramiko
from serial import Serial

from platformio.util import get_logicaldisks, get_serialports, get_systype


def FlushSerialBuffer(env, port):
    s = Serial(env.subst(port))
    s.flushInput()
    s.setDTR(False)
    s.setRTS(False)
    sleep(0.1)
    s.setDTR(True)
    s.setRTS(True)
    s.close()


def TouchSerialPort(env, port, baudrate):
    if "windows" not in get_systype():
        try:
            s = Serial(env.subst(port))
            s.close()
        except:  # pylint: disable=W0702
            pass
    s = Serial(port=env.subst(port), baudrate=baudrate)
    s.setDTR(False)
    s.close()
    sleep(0.4)


def WaitForNewSerialPort(env, before):
    new_port = None
    elapsed = 0
    while elapsed < 10:
        now = [i['port'] for i in get_serialports()]
        diff = list(set(now) - set(before))
        if diff:
            new_port = diff[0]
            break

        before = now
        sleep(0.25)
        elapsed += 0.25

    if not new_port:
        env.Exit("Error: Couldn't find a board on the selected port. "
                 "Check that you have the correct port selected. "
                 "If it is correct, try pressing the board's reset "
                 "button after initiating the upload.")

    return new_port


def AutodetectUploadPort(env):
    if "UPLOAD_PORT" in env:
        return

    if env.subst("$FRAMEWORK") == "mbed":
        msdlabels = ("mbed", "nucleo", "frdm")
        for item in get_logicaldisks():
            if (not item['name'] or
                    not any([l in item['name'].lower() for l in msdlabels])):
                continue
            env.Replace(UPLOAD_PORT=item['disk'])
            break
    else:
        board_build_opts = env.get("BOARD_OPTIONS", {}).get("build", {})
        for item in get_serialports():
            if "VID:PID" not in item['hwid']:
                continue
            env.Replace(UPLOAD_PORT=item['port'])
            for hwid in board_build_opts.get("hwid", []):
                board_hwid = ("%s:%s" % (hwid[0], hwid[1])).replace("0x", "")
                if board_hwid in item['hwid']:
                    break

    if "UPLOAD_PORT" in env:
        print "Auto-detected UPLOAD_PORT/DISK: %s" % env['UPLOAD_PORT']
    else:
        env.Exit("Error: Please specify `upload_port` for environment or use "
                 "global `--upload-port` option.\n"
                 "For some development platforms this can be a USB flash "
                 "drive (i.e. /media/<user>/<device name>)\n")


def UploadToDisk(_, target, source, env):  # pylint: disable=W0613,W0621
    env.AutodetectUploadPort()
    for ext in ("bin", "hex"):
        fpath = join(env.subst("$BUILD_DIR"), "firmware.%s" % ext)
        if not isfile(fpath):
            continue
        copyfile(fpath, join(env.subst("$UPLOAD_PORT"), "firmware.%s" % ext))
    print("Firmware has been successfully uploaded.\n"
          "Please restart your board.")


def UploadToSSH(_, target, source, env):  # pylint: disable=W0613,W0621

    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    params = urlparse("ssh://%s" % env.subst("$UPLOAD_PORT"))

    if not all([params.hostname, params.username, params.password]):
        env.Exit(
            "Error: Please check your SSH connection options "
            "in platformio.ini file")

    ssh_port = 22
    if params.port:
        ssh_port = params.port

    print "Connecting to %s:%d..." % (params.hostname, ssh_port)

    try:
        ssh_client.connect(
            params.hostname,
            port=ssh_port,
            username=params.username,
            password=params.password,
            timeout=5
        )

    except paramiko.AuthenticationException:
        env.Exit("Error: Authentication failed when connecting to %s" %
                 params.hostname)
    except Exception as e:  # pylint: disable=broad-except
        env.Exit("Error: Failed to connect to %s:%d: %s" %
                 (params.hostname, ssh_port, e))

    prog_name = env.subst("platformio$PROGSUFFIX")
    print "Uploading %s..." % prog_name
    ssh_client.exec_command("pkill %s" % prog_name, timeout=5)
    sleep(0.5)
    sftp_client = ssh_client.open_sftp()
    sftp_client.put(env.subst(source)[0], "/tmp/%s" % prog_name)
    sleep(0.5)
    sftp_client.chmod("/tmp/%s" % prog_name, 777)
    sleep(0.5)
    sftp_client.close()
    print "Start executing..."
    command = "nohup %s > /dev/null 2>&1 &" % "/tmp/%s" % prog_name
    ssh_client.exec_command(command, timeout=5)
    sleep(0.5)
    ssh_client.close()
    print "Uploading completed!"


def exists(_):
    return True


def generate(env):
    env.AddMethod(FlushSerialBuffer)
    env.AddMethod(TouchSerialPort)
    env.AddMethod(WaitForNewSerialPort)
    env.AddMethod(AutodetectUploadPort)
    env.AddMethod(UploadToDisk)
    env.AddMethod(UploadToSSH)
    return env
