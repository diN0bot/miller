#!/bin/sh
#
# Run this script:
#    ./diff_view_mac.sh
#
# This script uses FileMerge, a Mac OS XCode application,
# to view side-by-side differences between local changes 
# and the repository head.
#
# More details can be found here
#    http://kerneltrap.org/mailarchive/git/2007/11/21/435536
# include reasons why this is a BAD SOLUTION. eit.

#
# Filemerge.app must not already be open before running
# this script, or opendiff below will return immediately,
# and the TMPDIRs deleted before it gets the chance to read
# them.
#
#

if test $# = 0; then
   OLD=`git-write-tree`
elif test "$1" = --cached; then
   OLD=HEAD
   NEW=`git-write-tree`
   shift
fi
if test $# -gt 0; then
   OLD="$1"; shift
fi
test $# -gt 0 && test -z "$CACHED" && NEW="$1"

TMPDIR1=`mktemp -d`
git-archive --format=tar $OLD | (cd $TMPDIR1; tar xf -)
if test -z "$NEW"; then
   TMPDIR2=$(git rev-parse --show-cdup)
   test -z "$cdup" && TMPDIR2=.
else
   TMPDIR2=`mktemp -d`
   git-archive --format=tar $NEW | (cd $TMPDIR2; tar xf -)
fi

opendiff $TMPDIR1 $TMPDIR2 | cat
rm -rf $TMPDIR1
test ! -z "$NEW" && rm -rf $TMPDIR2
