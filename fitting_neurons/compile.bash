for i in *.tex;
do pdflatex -interaction=non-stop-mode -output-directory=./out $i;
done
# pdflatex -interaction=non-stop-mode e1.tex
