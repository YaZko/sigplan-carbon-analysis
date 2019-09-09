paper: sigplan_climate/main.tex
	cd sigplan_climate;\
	pdflatex main;\
	mv main.pdf ../sigplan_climate_data_analysis.pdf

draft_Y: draft_Yannick/old_draft.tex
	cd draft_Yannick;\
	pdflatex old_draft;\
	mv old_draft.pdf ../draft_Yannick.pdf

draft_C: draft_Crista/main.tex
	cd draft_Crista;\
	pdflatex main;\
	mv main.pdf ../draft_Crista.pdf

all:
	$(MAKE) paper
	$(MAKE) draft_Y
	$(MAKE) draft_C
