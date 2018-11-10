# Structure of the mirror-to-be

A mirror would probably consist of the following directories:

## `releases` &rarr; `https://nixos.org/releases`

### Contents

- Releases of Nix-related tools
- `nix`, `nixops`, `patchelf`

### Cloning

- Download using web crawler and update (re-fetch) according to 'Last-Modified'

## `channels` &rarr; `https://nixos.org/channels`

### Contents

- Latest version of all channels
- For `nix-channel --update`
- Contains `iso` images and `ova` appliances for NixOS.

### Cloning

- Download using web crawler and update (re-fetch) according to 'Last-Modified'
- Should we include old channels (like `13.10`)?

## `binary-cache` &rarr; `https://cache.nixos.org`

### Contents

- Binary archive closure of channels
  - Might need to get older releases of channels. Example: if `nixpkgs-unstable` updated twice between polls (`A` &rarr; `B` &rarr; `C`), we want to get closure of `B` as well, because some users might still be on `B`
- `$channel/store-paths.xz` &rarr; Find closure &rarr; Download all `.narinfo` and `.nar.{xz,bz2}`
  - Turns out `store-paths.xz` is not closure. Nothing much we can do, I think
- What do we do with `nixpkgs-{year}.{month}-darwin` channels? What are they?

### Cloning

- Steps:
  - Uncompress new `store-paths.xz` files
  - Find closures
  - Download `.nar.{xz,bz2}` files and write down corresponding `.narinfo` files
  - May require http server rewriting if downloading to filesystem
- Requires special scripts
  - If we avoid using Nix itself, when the scripts break it could be fixed by others that are not familiar with Nix
  - `https://cache.nixos.org` has a pretty simple format
