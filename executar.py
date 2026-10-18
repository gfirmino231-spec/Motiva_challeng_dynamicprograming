"""Reexecuta somente o notebook desta disciplina."""
from pathlib import Path
import nbformat
from nbclient import NotebookClient

if __name__ == '__main__':
    raiz = Path(__file__).resolve().parent
    caminho = raiz / 'notebook.ipynb'
    nb = nbformat.read(caminho, as_version=4)
    NotebookClient(nb, timeout=900, kernel_name='python3',
                   resources={'metadata': {'path': str(raiz)}}).execute()
    nbformat.write(nb, caminho)
    print('Notebook executado sem erros.')
