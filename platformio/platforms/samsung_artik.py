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

from platformio.platforms.base import BasePlatform


class Samsung_artikPlatform(BasePlatform):

    """
    Samsung ARTIK is the end-to-end, integrated IoT platform that transforms
    the process of building, launching, and managing IoT products. With an
    entire integrated ecosystem, from silicon to development tools to cloud,
    plus an extensive array of technology and development partners, you can
    shorten your development cycle to a degree you never thought possible.

    https://www.artik.io/
    """

    PACKAGES = {

        "toolchain-gccarma8gnueabihf": {
            "alias": "toolchain",
            "default": True
        },

        "framework-arduinolinuxarm": {
            "alias": "framework"
        },

        "tool-linuxuploader": {
            "alias": "uploader"
        }
    }

    def get_name(self):
        return "Samsung Artik"
