pdflatex -output-directory=out main.tex
biber --input-directory out --output-directory out main
pdflatex -output-directory=out main.tex
