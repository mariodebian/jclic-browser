#!/bin/bash


USER=$1

mkdir -p /home/${USER}/JClic/projects

cat << EOF > /home/${USER}/JClic/jclic.cfg
<?xml version="1.0" encoding="UTF-8"?>
<JClicSettings>
 <libraryManager autoRun="true">
  <library name="Main library" path="/home/${USER}/JClic/projects/library.jclic" />
 </libraryManager>
 <language id="es" />
 <paths>
  <path id="root" path="/home/${USER}/JClic/projects" />
 </paths>
 <reporter enabled="false" class="TCPReporter" params="path=localhost:9000" />
 <sound enabled="true" system="true" mediaSystem="default" />
 <lookAndFeel id="system" />
 <browser id="" />
 <skin id="@default.xml" />
 <recentFiles />
</JClicSettings>
EOF

chown -R ${USER} /home/${USER}/JClic
chown -R ${USER}:${USER} /home/${USER}/JClic

