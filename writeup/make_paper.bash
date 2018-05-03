pdflatex -output-directory=out conference.tex
biber --input-directory out --output-directory out conference
pdflatex -output-directory=out conference.tex
