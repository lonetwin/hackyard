# Collection of functions / script and random bash stuff

Stuff that's scattered around my dotfiles

* [mount-fu.sh](./mount-fu.sh)
  
  I like a [FUSE](https://www.kernel.org/doc/html/next/filesystems/fuse.html) filesystems. These functions are wrappers around various fuse mount tools. The functions assume the tools (eg: [s3fs](https://github.com/s3fs-fuse/s3fs-fuse), [fuse-archive](https://github.com/google/fuse-archive) ..etc) are installed. You may choose also to export an env var `$MOUNTS_HOME` as the base dir for mounts. (currently defined: `mount_s3fs, mount_sshfs, mount_archive`)
