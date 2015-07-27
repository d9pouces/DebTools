DebTools
========

`deb-dep-tree`
--------------

Show the dependencies of a given package:

    deb-dep-tree libgcc1_4.7.2-5_amd64.deb 
    libgcc1
    =======
    
      * multiarch-support 
      * gcc-4.7-base (= 4.7.2-5)
      * libc6 (>= 2.2.5)

Ok, nothing new from the standard `dpkg -I libgcc1_4.7.2-5_amd64.deb` command.
However, you can provide a package name or a .deb filename:

    deb-dep-tree libgcc1 
    Réception de : 1 Téléchargement de libgcc1 1:4.7.2-5 [43,1 kB]
    43,1 ko réceptionnés en 0s (45,2 ko/s)            
    libgcc1
    =======
    
      * multiarch-support 
      * gcc-4.7-base (= 4.7.2-5)
      * libc6 (>= 2.2.5)

The package will be downloaded in the current directory.
Do you want to recursively retrieve dependencies?

    dpkg -l | grep libc > /tmp/toignore
    deb-dep-tree libgcc1 -r -i /tmp/toignore
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
    
    
Sometimes, there is a choice between several possibilities for a given dependency. These dependencies are ignored (since we cannot select one).
However, you can use the `-l` flag to select choices which are currently installed on the system.
You can also ignore some dependencies, by providing a file with a list of dependencies to ignore. Its format is the same as the output of the `dpkg -l` command.


deb-dep-tree = debtools.debdeptree:main',
                                    'multiple-deb = debtools.multideb:main'