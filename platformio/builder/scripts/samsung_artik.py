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

"""
    Builder for Samsung Artik CPUs
"""

from os.path import join

from SCons.Script import (AlwaysBuild, Default, DefaultEnvironment)

from platformio.util import get_systype


env = DefaultEnvironment()

env.Replace(
    _BINPREFIX="",
    AR="${_BINPREFIX}ar",
    AS="${_BINPREFIX}as",
    CC="${_BINPREFIX}gcc",
    CXX="${_BINPREFIX}g++",
    OBJCOPY="${_BINPREFIX}objcopy",
    RANLIB="${_BINPREFIX}ranlib",
    SIZETOOL="${_BINPREFIX}size",

    SIZEPRINTCMD='"$SIZETOOL" $SOURCES'
)

if "arm" not in get_systype():
    env.Replace(
        _BINPREFIX="arm-cortex_a8-linux-gnueabihf-",

        UPLOADER=join("$PIOPACKAGES_DIR", "tool-linuxuploader", "linuxloader"),
        UPLOADERFLAGS=["push"],
        UPLOADCMD='"$UPLOADER" $UPLOADERFLAGS $SOURCES "$UPLOAD_PORT"',

        PROGNAME="firmware",
        PROGSUFFIX=".elf"
    )

if "arduino" in env.subst("$FRAMEWORK"):
    env.Replace(
        ARFLAGS=["rcs"],

        ASFLAGS=["-x", "assembler-with-cpp"],

        CCFLAGS=[
            "-g",
            "-Wall",
            "-nostdlib"
        ],

        LINKFLAGS=[
            "-Wall",
            "-Wl,--gc-sections"
        ],

        LIBS=["rt", "pthread"],

        SIZEPRINTCMD='"$SIZETOOL" -B -d $SOURCES',
    )


#
# Target: Build executable and linkable firmware
#

target_elf = env.BuildProgram()

#
# Target: Print binary size
#

target_size = env.Alias("size", target_elf, "$SIZEPRINTCMD")
AlwaysBuild(target_size)

#
# Target: Upload firmware
#

if env.subst("$UPLOAD_PROTOCOL") == "ssh":
    target_upload = env.Alias(
        ["upload", "uploadlazy"], target_elf, env.UploadToSSH)
else:
    target_upload = env.Alias(
        ["upload", "uploadlazy"], target_elf,
        [lambda target, source, env: env.AutodetectUploadPort(), "$UPLOADCMD"])
AlwaysBuild(target_upload)

#
# Target: Test
#

AlwaysBuild(env.Alias("test", target_elf))

#
# Target: Define targets
#

Default([target_elf, target_size])
