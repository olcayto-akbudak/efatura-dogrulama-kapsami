.PHONY: all bases run figures clean

all: bases run figures

bases:
	python -m src.bases

run:
	python -m src.run > /dev/null
	@python -c "import json;o=json.load(open('reports/ozet.json'));print('Mutasyon:',o['mutasyon'],'| resmî yakalama: %',o['resmi_yakalama_pct'],'| hiçbiri:',o['kacirilan_hicbiri'])"

figures:
	python -m src.figures

clean:
	rm -rf mutants reports/*.csv reports/*.json reports/figures/*.png
