#!/usr/bin/python
# coding=utf-8
# Released under the New BSD licence:

# Copyright (c) 2011 Massachusetts Institute of Technology.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the Massachusetts Institute of Technology nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


"""Attempts to package an executable .py script along with the
non-system modules that it imports. See:

http://evanjones.ca/software/packagepy.html

缺陷
  安装了一个第三方库 一个文件 import 了之后,无法把这个第三方库加入进来

还不能商用

"""

__author__ = "Evan Jones <evanj@csail.mit.edu>"

import modulefinder
import os
import sys
import zipfile
import stat


def notBuiltInModules(script_path):
    """Returns a list of (module, path) pairs that are not built-in modules."""
    # Figure out the paths for "built-in" modules:
    # Remove any paths in PYTHONPATH, as those are clearly not "built-in"
    # sys.path[0] is the "script path": ignore it
    pythonpaths = set({})
    if "PYTHONPATH" in os.environ:
        for path in os.environ["PYTHONPATH"].split(os.pathsep):
            pythonpaths.add(path)
    system_paths = []
    for path in sys.path[1:]:
        if path not in pythonpaths:
            system_paths.append(path)
    #~ print "system paths:", "; ".join(system_paths)

    finder = modulefinder.ModuleFinder()
    finder.run_script(script_path)
    finder.report()

    not_builtin = []
    for name, module in finder.modules.iteritems():
        # The _bisect module has __file__ = None
        if not hasattr(module, "__file__") or module.__file__ is None:
            # Skip built-in modules
            continue

        system_module = False
        for system_path in system_paths:
            if module.__file__.startswith(system_path):
                system_module = True
                break
        if system_module:
            continue

        # Skip the script
        if name == "__main__":
            assert module.__file__ == script_path
            continue

        relative_path = name.replace('.', '/')
        if module.__path__:
            #~ # This is a package; originally I skipped it, but that is not a good idea
            assert module.__file__.endswith("/__init__.py")
            relative_path += "/__init__.py"
        else:
            relative_path += os.path.splitext(module.__file__)[1]

        assert name != "__main__"
        not_builtin.append((module.__file__, relative_path))
    return not_builtin


def main(script_path, output_path):
    if os.path.exists(output_path):
        raise ValueError("output path '%s' exists; refusing to overwrite\n" % output_path)

    not_builtin = notBuiltInModules(script_path)

    # We make a zip! We start with a Python header
    outfile = open(output_path, 'w+b')
    outfile.write("#!/usr/bin/env python\n")
    outfile.flush()
    # outfile.close() # cannot close, the Zipfile will error

    outzip = zipfile.ZipFile(outfile, 'a', zipfile.ZIP_DEFLATED)
    #~ outzip = zipfile.ZipFile(output_path, 'a', zipfile.ZIP_DEFLATED)

    # TODO: Save compiled python (.pyc or .pyo) instead of source? Bytecode may
    # not be compatible between versions though?
    outzip.write(script_path, "__main__.py")
    for source_path, relative_destination_path in not_builtin:
        outzip.write(source_path, relative_destination_path)
    outzip.close()



if __name__ == "__main__":

    a= os.path.realpath(__file__)
    a = os.path.dirname(a)

    b = os.path.join(a,'gamecc_conf.usage.py.pyz')
    if os.path.exists(b):
        os.remove(b)

    sys.argv.append(os.path.join(a,'gamecc_conf.usage.py'))
    sys.argv.append(b)

    if len(sys.argv) != 3:
        sys.stderr.write("packagepy.py (script to package) (package output)\n")
        sys.exit(1)
    script_path = sys.argv[1]
    output_path = sys.argv[2]

    main(script_path, output_path)

