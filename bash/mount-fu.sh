#!/bin/bash

MOUNTS_HOME=${HOME}/mounts    # - where fuse mounts are created

function mount_s3fs {
    local USAGE="Usage: mount_s3fs [-h | <bucket> [mountpoint]]"

    # - with no argument, print out any existing s3fs mounts
    [ "$#" -lt 1 ] && mount -t fuse.s3fs && return
    [ "$1" == "-h" ] && echo $USAGE && return

    # - if already mounted, reminds us about this
    if $(grep -q ${1} <(mount -t fuse.s3fs) 2> /dev/null); then
        mount -t fuse.s3fs
        return
    fi

    if [[ -z $AWS_PROFILE ]]; then
        echo "Not logged in ?"
        return
    elif [[ -z $AWS_SESSION_TOKEN ]]; then
        eval $(aws configure export-credentials --format env)
    fi

    local srcpath="${1}"
    local destdir="${2:-${MOUNTS_HOME}/s3fs/${srcpath}}"
    [ -d "${destdir}" ] || mkdir -p "${destdir}" && s3fs "${srcpath}" "${destdir}" && mount_s3fs
}

function mount_sshfs {
    # executes "sshfs host:/dest/path /home/steve/src/sshfs/dest/path",
    # creating the mountpoint, if necessary. If leading / in /dest/path is
    # missing, the path is relative to ~ on the destination
    local USAGE="Usage: mount_sshfs [-h | <hostname>[:path] [mountpoint]]"

    # - with no argument, print out any existing sshfs mounts
    [ "$#" -lt 1 ] && mount -t fuse.sshfs && return
    [ "$1" == "-h" ] && echo $USAGE && return

    local srcpath="${1}"
    local destdir="${2:-${MOUNTS_HOME}/sshfs/${srcpath/:*/}/${srcpath/*:/}}"
    [ -d "${destdir}" ] || mkdir -p "${destdir}" && sshfs "${srcpath}" "${destdir}"
}
complete -F _known_hosts -S: mount_sshfs

function mount_archive {
    local USAGE="Usage: mount_archive [-h | [-o <opt> ...] <archive>]"

    # - with no argument, print out any existing archive mounts
    [ "$#" -lt 1 ] && mount -t fuse.fuse-archive && return
    [ "$1" == "-h" ] && echo $USAGE && return

    default_opts="-o lazycache,direct_io,noxattrs,noatime,clone_fd"

    last_arg="${@: -1}"

    if [[ -d ${last_arg} ]]; then
        fuse-archive ${default_opts} "${@}"
    else
        archive=$(basename "${last_arg}")
        destdir="${MOUNTS_HOME}/archive/${archive%%.*}"
        fuse-archive ${default_opts} "${@}" ${destdir}
    fi
}
# XXX note: expansion needs `extglob` to be enabled for your shell (ie: shopt-s extglob)
complete -f -o plusdirs -X '!*.@(7z|7zip|a|ar|cab|cpio|deb|iso|iso9660|jar|mtree|rar|rpm|tar|war|warc|xar|zip|zipx|crx|odf|odg|odp|ods|odt|docx|ppsx|pptx|xlsx|tb2|tbr|tbz|tbz2|tz2|tgz|tlz|tlz4|tlzma|txz|tz|taz|tzs|tzst|tzstd|br|brotli|bz2|bzip2|grz|grzip|gz|gzip|lha|lrz|lrzip|lz|lz4|lzip|lzma|lzo|lzop|xz|z|zst|zstd|b64|base64|uu|asc|gpg|pgp)'
