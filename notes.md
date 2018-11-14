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
- `binary-cache-url`: Replace with mirror's

### Cloning

- Download using web crawler and update (re-fetch) according to 'Last-Modified'
- Should we include old channels (like `13.10`)?

## `binary-cache` &rarr; `https://cache.nixos.org`

### Contents

- Binary archive closure of channels
  - Option A:
    - Might need to get older releases of channels. Example: if `nixpkgs-unstable` updated twice between polls (`A` &rarr; `B` &rarr; `C`), we want to get closure of `B` as well, because some users might still be on `B`
    - `https://channels.nix.gsc.io/` provides historical channel URLs and timestamps (of commit). Shoutout to @grahamc.
  - Option B:
    - We only update channels to the newest version at time of synchronization
      - Atomicity: Read the HTTP 302 redirection once, use it for all file downloads
    - We simply do not care about missed channels
    - Store a 'last touched' time for all entries
      - Cache eviction by 'Least recently touched'
    - Property: If user only uses `$mirror/channels`, the '`A` &rarr; `B` &rarr; `C` problem' in option A never occurs
    - Users should either:
      - *Not* use `https://nixos.org/channels`, or
      - Use `https://nixos.org/channels` and accept that some substitutions will be from `https://cache.nixos.org`
- `$channel/store-paths.xz` &rarr; Find closure &rarr; Download all `.narinfo` and `.nar.{xz,bz2}`
  - Turns out `store-paths.xz` is not closure. Nothing much we can do, I think
- What do we do with `nixpkgs-{year}.{month}-darwin` channels? What are they?

### Cloning

- Steps:
  - Option A:
    - Find recent channel releases. Check `Released on {date} {time} from` line.
  - Option B:
    - Use latest channel releases only
  - Uncompress new `store-paths.xz` files
  - Find closures
  - Download `.nar.{xz,bz2}` files and write down corresponding `.narinfo` files
  - May require http server rewriting if downloading to filesystem
- Requires special scripts
  - If we avoid using Nix itself, when the scripts break it could be fixed by others that are not familiar with Nix
  - `https://cache.nixos.org` has a pretty simple format
