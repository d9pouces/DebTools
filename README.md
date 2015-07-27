DebTools
========

`deb-dep-tree`
--------------

Download packages and show the dependencies of a given package:

    $ deb-dep-tree libgcc1_4.7.2-5_amd64.deb 
    libgcc1
    =======
    
      * multiarch-support 
      * gcc-4.7-base (= 4.7.2-5)
      * libc6 (>= 2.2.5)

Ok, nothing new from the standard `dpkg -I libgcc1_4.7.2-5_amd64.deb` command, but you can provide either a package name or a .deb filename:

    $ deb-dep-tree libgcc1 
    Réception de : 1 Téléchargement de libgcc1 1:4.7.2-5 [43,1 kB]
    43,1 ko réceptionnés en 0s (45,2 ko/s)            
    libgcc1
    =======
    
      * multiarch-support 
      * gcc-4.7-base (= 4.7.2-5)
      * libc6 (>= 2.2.5)

The package will be downloaded in the current directory. You can recursively retrieve all dependencies.

    $ deb-dep-tree libgcc1 -r
    libgcc1
    =======
    
      * multiarch-support 
      * gcc-4.7-base (= 4.7.2-5)
      * libc6 (>= 2.2.5)
    
    multiarch-support
    =================
    
      * libc6 (>= 2.3.6-2)
    
    libc-bin
    ========
    
    
    gcc-4.7-base
    ============
    
    
    libc6
    =====
    
      * libc-bin (= 2.13-38+deb7u8)
      * libgcc1 
      
    $ ls
    gcc-4.7-base_4.7.2-5_amd64.deb  libc6_2.13-38+deb7u8_amd64.deb  libc-bin_2.13-38+deb7u8_amd64.deb  libgcc1_4.7.2-5_amd64.deb  multiarch-support_2.13-38+deb7u8_amd64.deb



Sometimes, there is a choice between several possibilities for a given dependency. These dependencies are ignored (since we cannot select one).
However, you can use the `-l` flag to select choices which are currently installed on the system.

    $ dpkg -I libssl1.0.0_1.0.1e-2+deb7u17_amd64.deb | grep Depends
    Pre-Depends: multiarch-support
    Depends: libc6 (>= 2.7), zlib1g (>= 1:1.1.4), debconf (>= 0.5) | debconf-2.0
    
    $ dpkg -l | grep debconf
    ii  debconf                            1.5.49                        all          Debian configuration management system
    ii  debconf-i18n                       1.5.49                        all          full internationalization support for debconf
    ii  po-debconf                         1.0.16+nmu2                   all          tool for managing templates file translations with gettext

    $ deb-dep-tree libssl1.0.0
    libssl1.0.0
    ===========
    
      * multiarch-support 
      * zlib1g (>= 1:1.1.4)
      * libc6 (>= 2.7)
    
    $ deb-dep-tree libssl1.0.0 -l
    libssl1.0.0
    ===========
    
      * debconf 
      * multiarch-support 
      * zlib1g (>= 1:1.1.4)
      * libc6 (>= 2.7)

You can also ignore some dependencies, by providing a file with a list of dependencies to ignore. Its format is the same as the output of the `dpkg -l` command.

    $ dpkg -l | grep libc > /tmp/toignore
    $ deb-dep-tree libgcc1 -r -i /tmp/toignore
    libgcc1
    =======
    
      * multiarch-support 
      * gcc-4.7-base (= 4.7.2-5)
      * libc6 (>= 2.2.5)
    
    multiarch-support
    =================
    
      * libc6 (>= 2.3.6-2)
    
    gcc-4.7-base
    ============

