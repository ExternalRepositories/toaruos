#!/usr/bin/env python3
# coding: utf-8

import os
import sys

try:
    TOOLCHAIN_PATH = os.environ['TOOLCHAIN']
except KeyError:
    # This is not good, but we need to let it happen for the make file
    TOOLCHAIN_PATH = ""

force_static = []

class Classifier(object):

    dependency_hints = {
        # Toaru Standard Library
        '<toaru/kbd.h>':         (None, '-ltoaru_kbd',         []),
        '<toaru/list.h>':        (None, '-ltoaru_list',        []),
        '<toaru/hashmap.h>':     (None, '-ltoaru_hashmap',     ['<toaru/list.h>']),
        '<toaru/tree.h>':        (None, '-ltoaru_tree',        ['<toaru/list.h>']),
        '<toaru/pthread.h>':     (None, '-ltoaru_pthread',     []),
        '<toaru/pex.h>':         (None, '-ltoaru_pex',         []),
        '<toaru/graphics.h>':    (None, '-ltoaru_graphics',    []),
        '<toaru/drawstring.h>':  (None, '-ltoaru_drawstring',  ['<toaru/graphics.h>']),
        '<toaru/rline.h>':       (None, '-ltoaru_rline',       ['<toaru/kbd.h>']),
        '<toaru/confreader.h>':  (None, '-ltoaru_confreader',  ['<toaru/hashmap.h>']),
        '<toaru/dlfcn.h>':       (None, '-ltoaru_dlfcn',       []),
        '<toaru/yutani.h>':      (None, '-ltoaru_yutani',      ['<toaru/kbd.h>', '<toaru/list.h>', '<toaru/pex.h>', '<toaru/graphics.h>', '<toaru/hashmap.h>']),
        '<toaru/decorations.h>': (None, '-ltoaru_decorations', ['<toaru/graphics.h>', '<toaru/yutani.h>','<toaru/dlfcn.h>']),
        '<toaru/termemu.h>':     (None, '-ltoaru_termemu',     ['<toaru/graphics.h>']),
    }

    def __init__(self, filename):
        self.filename  = filename
        self.includes, self.libs = self._depends()

    def _calculate(self, depends, new):
        """Calculate all dependencies for the given set of new elements."""
        for k in new:
            if not k in depends:
                depends.append(k)
                _, _, other = self.dependency_hints[k]
                depends = self._calculate(depends, other)
        return depends

    def _sort(self, depends):
        """Sort the list of dependencies so that elements appearing first depend on elements following."""
        satisfied = []
        a = depends[:]

        while set(satisfied) != set(depends):
            b = []
            for k in a:
                if all([x in satisfied for x in self.dependency_hints[k][2]]):
                    satisfied.append(k)
                else:
                    b.append(k)
            a = b[:]
        return satisfied[::-1]

    def _depends(self):
        """Calculate include and library dependencies."""
        lines = []
        depends = []
        with open(self.filename,'r') as f:
            lines = f.readlines()
        for l in lines:
            if l.startswith('#include'):
                depends.extend([k for k in list(self.dependency_hints.keys()) if l.startswith('#include ' + k)])
        depends = self._calculate([], depends)
        depends = self._sort(depends)
        includes  = []
        libraries = []
        for k in depends:
            dep = self.dependency_hints[k]
            if dep[0]:
                includes.append('-I' + TOOLCHAIN_PATH + '/include/' + dep[0])
            if dep[1]:
                libraries.append(dep[1])
        return includes, libraries


def todep(name):
    """Convert a library name to an archive path or object file name."""
    if name.startswith("-l"):
        name = name.replace("-l","",1)
        if name in force_static:
            return (False, "%s/lib%s.a" % (TOOLCHAIN_PATH + '/lib', name))
        else:
            return (True, "%s/lib%s.so" % ('base/lib', name))
    else:
        return (False, name)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("usage: util/auto-dep.py command filename")
        exit(1)
    command  = sys.argv[1]
    filename = sys.argv[2]

    c = Classifier(filename)

    if command == "--cflags":
        print(" ".join([x for x in c.includes]))
    elif command == "--libs":
        print(" ".join([x for x in c.libs]))
    elif command == "--deps":
        results = [todep(x) for x in c.libs]
        normal = [x[1] for x in results if not x[0]]
        order_only = [x[1] for x in results if x[0]]
        print(" ".join(normal) + " | " + " ".join(order_only))
    elif command == "--make":
        print("base/bin/{app}: {source} | {libraryfiles} base/lib/libc.so\n\t$(CC) $(CFLAGS) -o $@ $< {libraries} $(LIBS)".format(
            app=os.path.basename(filename).replace(".c",""),
            source=filename,
            libraryfiles=" ".join([todep(x)[1] for x in c.libs]),
            libraries=" ".join([x for x in c.libs])))

