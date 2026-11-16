# 🛠️ Ferramenta: Organizador de Provas (PDF → Markdown)

Automatiza em lote o que foi feito manualmente com a prova de Brusque: lê todos os PDFs de uma pasta, extrai texto e imagens, detecta as questões e os **textos-base agrupados**, e gera um `.md` organizado por prova — repetindo o texto-base antes de cada questão vinculada a ele.

## ✅ O que a ferramenta faz

- Lê **todos os PDFs** de uma pasta de uma vez (700, 1000... tanto faz).
- Extrai o **texto** na ordem original e as **imagens** (pulando logos/marcas d'água repetidas).
- Detecta os cabeçalhos **"Questão NN"** (01, 02, 03...) e separa cada questão.
- Detecta avisos como *"O texto seguinte servirá de base para responder às questões 1 a 8"* e **repete o texto-base antes de cada questão do grupo**, marcando com 🔗.
- Gera, para cada PDF, uma pasta com:
  ```
  Nome_da_Prova/
  ├── Nome_da_Prova.md
  └── imagens/
      ├── pag005_img004.jpeg
      └── ...
  ```

## 📥 Como instalar (uma vez só)

1. Instale o **Python**: https://www.python.org/downloads/ (marque a opção **"Add Python to PATH"** na instalação).
2. Abra o **Prompt de Comando** (Windows) ou Terminal (Mac/Linux) e rode:
   ```
   pip install pymupdf
   ```
3. Baixe este repositório (botão verde **Code → Download ZIP**) e descompacte.

## ▶️ Como usar

1. Coloque todos os seus PDFs numa pasta, por exemplo `C:\provas\pdfs`.
2. No Prompt de Comando, dentro da pasta da ferramenta, rode:
   ```
   python organizador_provas.py --pasta C:\provas\pdfs --saida C:\provas\saida
   ```
3. Pronto: em `C:\provas\saida` estará um `.md` organizado por prova, com as imagens.
4. **(Opcional) Publicar direto no GitHub** — se você clonou este repositório:
   ```
   python organizador_provas.py --pasta C:\provas\pdfs --saida C:\provas\saida --repo C:\caminho\do\provas_md
   cd C:\caminho\do\provas_md
   git add -A
   git commit -m "Novas provas organizadas"
   git push
   ```

## ⚠️ Limitações importantes

- **PDFs escaneados** (foto/imagem, sem texto selecionável) não funcionam com esta ferramenta — eles precisam de OCR antes. Se o seu PDF permitir selecionar o texto com o mouse, funciona. Para escaneados, instale o OCR antes com:
  ```
  pip install ocrmypdf
  ocrmypdf entrada.pdf saida.pdf
  ```
- A extração é **automática e literal**: o `.md` sai fiel ao PDF, mas **sem a análise fina** que eu faço manualmente (identificar qual imagem pertence a qual questão, corrigir quebras de linha, descrever imagens, análise do agrupamento).
- A detecção do texto-base usa o aviso padrão das bancas ("servirá de base para responder às questões X a Y"). Bancas que não escrevem esse aviso terão as questões separadas, mas sem a repetição automática do texto-base.

## 💡 Fluxo recomendado com 700 provas

1. Rode a ferramenta no seu PC → ela gera tudo em minutos.
2. Publique no repositório `provas_md`.
3. Se quiser o **acabamento manual** (como o da prova de Brusque) em alguma prova específica — análise do agrupamento, imagens vinculadas às questões certas, descrição das imagens — me mande o PDF aqui que eu faço.

## 🧪 Testada com

- Prova Câmara Municipal de Brusque/SC 2024 (FURB) — 40/40 questões detectadas, 10 agrupamentos identificados, 6 imagens relevantes extraídas.
