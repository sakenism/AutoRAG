pip install 'AutoRAG[gpu]'
# pip install AutoRAG

pip uninstall chromadb
pip install chromadb==0.6.3

pip install --upgrade pyOpenSSL
pip install nltk
python3 -c "import nltk; nltk.download('punkt_tab')"
python3 -c "import nltk; nltk.download('averaged_perceptron_tagger_eng')"

