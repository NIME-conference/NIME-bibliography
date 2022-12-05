#!/usr/bin/env bash

mkdir -p release
cat > release/index.html <<End-Of-File-Delimiter
<html><head></head><body>
<h2>NIME Proceedings BibTeX Files</h2>
<ul>
<li><a href="nime_papers.bib">Combined Paper Proceedings (BibTeX Format)</a></li>
<li><a href="nime_music.bib">Combined Music Proceedings (BibTeX Format)</a></li>
<li><a href="nime_installation.bib">Combined Installation Proceedings (BibTeX Format)</a></li>
<li><a href="nime_papers.csv">Combined Paper Proceedings (CSV Format)</a></li>
<li><a href="nime_music.csv">Combined Music Proceedings (CSV Format)</a></li>
<li><a href="nime_installation.csv">Combined Installation Proceedings (CSV Format)</a></li>
<li><a href="nime_papers.yaml">Combined Paper Proceedings (YAML Format)</a></li>
<li><a href="nime_music.yaml">Combined Music Proceedings (YAML Format)</a></li>
<li><a href="nime_installation.yaml">Combined Installation Proceedings (YAML Format)</a></li>
<li><a href="nime_papers.json">Combined Paper Proceedings (JSON Format)</a></li>
<li><a href="nime_music.json">Combined Music Proceedings (JSON Format)</a></li>
<li><a href="nime_installation.json">Combined Installation Proceedings (JSON Format)</a></li>
</ul>
<p>Source available at <a href="https://github.com/NIME-conference/NIME-bibliography">the NIME-bibliography repository.</a></p>
<p>More information at <a href="https://nime.org">nime.org</a></p>
</body></html>
End-Of-File-Delimiter
