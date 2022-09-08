#!/usr/bin/env bash

mkdir -p release
cat > release/index.html <<End-Of-File-Delimiter
<html><head></head><body>
<h2>NIME Proceedings BibTeX Files</h2>
<ul>
<li><a href="nime_papers.bib">Combined Paper Proceedings (BibTeX Format)</a></li>
<li><a href="nime_music.bib">Combined Music Proceedings (BibTeX Format)</a></li>
<li><a href="nime_installation.bib">Combined Installation Proceedings (BibTeX Format)</a></li>
</ul>
<p>Source available at <a href="https://github.com/NIME-conference/NIME-bibliography">the NIME-bibliography repository.</a></p>
<p>More information at <a href="https://nime.org">nime.org</a></p>
</body></html>
End-Of-File-Delimiter
