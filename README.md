# Portfólio — Rafael Inácio

Portfólio pessoal de **Rafael Inácio**, Engenheiro de IA e Desenvolvedor Backend Python.
É um site minimalista e editorial feito com **HTML, CSS e JavaScript puro**, sem framework e sem etapa de build.

Todo o conteúdo, em português e inglês, fica em arquivos JSON. O código só sabe *como* desenhar a página e não guarda nenhum texto.

---

## Como rodar

O site carrega os JSON com `fetch()` e usa módulos ES. Por isso precisa de um servidor HTTP: abrir o `index.html` direto no navegador (`file://`) não funciona.

```bash
# qualquer servidor estático serve, por exemplo:
python -m http.server 8000
# ou
npx serve .
```

Depois é só abrir `http://localhost:8000`. Para ver a versão em inglês, use `http://localhost:8000/?lang=en`.

Para publicar, envie a pasta como está para qualquer hospedagem estática (GitHub Pages, Netlify, Vercel…).

---

## Estrutura

```
.
├── index.html            → página inicial (casca vazia)
├── escritos.html         → página de artigos (mesma casca, data-pagina="escritos")
├── data.json             → todo o conteúdo em português
├── data.en.json          → o mesmo conteúdo em inglês (mesma estrutura)
├── style.css             → design system e estilos (tokens, temas, assinaturas)
├── assets/
│   ├── docs/             → currículo em PDF
│   └── img/icons/        → desenhos das "curiosidades"
├── js/
│   ├── main.js           → ponto de entrada
│   ├── app/              → orquestração (PortfolioApp, MetaManager)
│   ├── services/         → dados e APIs (data.json, Medium, área de transferência)
│   ├── components/       → uma classe por bloco da página
│   ├── features/         → comportamentos globais (tema, idioma, curiosidades, rolagem)
│   ├── ui/               → peças reutilizáveis (Link, Announcer)
│   └── core/             → funções puras (criação de DOM, utilitários)
└── tools/
    └── doodle_icons.py   → gerador dos ícones desenhados à mão
```

---

## Conceitos

### 1. Arquitetura orientada a dados (data-driven)

A regra principal do projeto é **não escrever texto de conteúdo no HTML nem no JavaScript**.
Os arquivos `index.html` e `escritos.html` são só uma casca com áreas vazias (`nav`, `header`, `main`, `footer`). Tudo o que aparece na tela vem do `data.json`, que está dividido em coleções:

| Coleção        | O que guarda                                                  |
| -------------- | ------------------------------------------------------------- |
| `perfil`       | nome, cargo, bio, links, contatos e ferramentas               |
| `trajetoria`   | experiência, formação, cursos e certificações                 |
| `projetos`     | projetos, opcionalmente agrupados por `categoria`             |
| `escritos`     | artigos salvos + configuração do feed do Medium               |
| `curiosidades` | desenhos pessoais que aparecem nas margens, e o ritmo deles   |
| `textos`       | títulos, rótulos, menu, metadados (SEO) e textos de acessibilidade |

Mesmo os elementos fixos do HTML pegam o texto do JSON, através dos atributos `data-texto="caminho"` e `data-aria="caminho"` (veja o `MetaManager`).

**Resiliência:** o `PortfolioService` normaliza os dados para que todas as coleções sempre existam. Toda seção herda de `Section`, que não desenha nada quando o conteúdo está vazio. Remover um array do JSON esconde a seção, sem quebrar a página.

### 2. Componentes em JavaScript puro

Cada bloco da página é uma classe que herda de `Component`. Ela recebe `(data, services)` e implementa `render()`.
O `PortfolioApp` faz o papel de maestro: um mapa `PAGES` diz quais componentes compõem cada página e em que ordem.

```js
static PAGES = {
  inicio:   { header: Hero,           sections: [About, Projects, Timeline, Skills, Contact] },
  escritos: { header: WritingsHeader, sections: [WritingsArchive] },
};
```

Para reordenar ou esconder uma seção, basta editar essa lista. Para criar uma página nova, adicione uma entrada em `PAGES` e um HTML com `<body data-pagina="chave">`.

### 3. Segurança na renderização

A interface inteira é montada com `createElement()` (`js/core/dom.js`). Todo texto vindo do JSON ou do Medium entra como `textContent`, **nunca como HTML**. Assim, um `<script>` escrito dentro de um artigo aparece como texto e não é executado.

### 4. Internacionalização (PT/EN)

Existe um arquivo de dados por idioma, todos com a mesma estrutura. O `LanguageSwitcher` escolhe o idioma nesta ordem de prioridade:

1. `?lang=en` no endereço;
2. a escolha feita no botão, salva no navegador;
3. o idioma do navegador.

Para mudar um texto, edite **os dois** arquivos.

### 5. Escritos ao vivo do Medium

Os artigos salvos no `data.json` aparecem na hora. Em segundo plano, o `MediumService` busca o feed do Medium via [rss2json](https://rss2json.com). O conversor é necessário porque o RSS do Medium não envia cabeçalhos CORS. Os artigos novos são juntados com os salvos, e só as seções marcadas com `static updatesWithMedium = true` são redesenhadas. Se o Medium estiver fora do ar, o site continua com a lista do JSON.

### 6. Design system e temas

O `style.css` começa com **design tokens** em `:root`: tipografia, escala de espaçamento de 4px, largura de leitura (`--measure: 660px`) e cores.

- **Claro/escuro automático** via `prefers-color-scheme`.
- **Escolha manual** pelo `ThemeSwitcher`, gravada em `<html data-theme>`, que tem prioridade sobre o sistema. Um script curto no `<head>` reaplica a escolha antes da página aparecer, para não piscar o tema errado.
- **Tipografia editorial:** Newsreader (serifa, para leitura) e Inter (interface). As fontes são carregadas sem bloquear a página.

### 7. Assinaturas visuais

Três detalhes sutis dão identidade ao site:

1. **Cursor de redação.** O loader é só um cursor piscando, e ele também aparece no topo das páginas, como quem está escrevendo.
2. **Marca-texto nos links.** No hover, o link ganha um realce verde, como uma caneta marca-texto. Links externos ganham a seta ↗.
3. **O ■ de fim de matéria.** A trajetória é um fio vertical com marcadores ■, e um ■ verde fecha a página, como no fim de uma reportagem impressa. O mesmo ■ é o favicon.

### 8. Curiosidades nas margens

De tempos em tempos, um desenho feito à mão surge na margem da página. Ao passar o mouse, aparece uma curiosidade sobre o Rafael (anime favorito, time, músicas…). Os tempos são sorteados, a ordem é embaralhada e nada se repete até todos terem aparecido. A configuração fica em `data.curiosidades`.

Os ícones são gerados pelo script `tools/doodle_icons.py`, que precisa de Python e Pillow:

```bash
pip install pillow
python tools/doodle_icons.py
```

### 9. Navegação por rolagem além da borda

Na página inicial, quem chega ao fim e continua rolando vai para **Escritos**. Na página de Escritos, quem rola para cima além do topo volta ao início, já posicionado no fim da página. Um aviso discreto com uma barra de progresso evita trocas de página acidentais: a página só muda se a pessoa insistir.

### 10. Acessibilidade e performance

- Link "pular para o conteúdo", `aria-labelledby` nas seções e `aria-current` no menu.
- Região `aria-live` que anuncia ações aos leitores de tela (ex.: "Copiado" ao copiar o e-mail).
- Respeito a `prefers-reduced-motion`.
- `modulepreload` de todos os módulos, para que o navegador baixe tudo em paralelo.
- Nenhuma dependência de JavaScript e nenhum bundler: o site entrega exatamente o código que está no repositório.

---

## Editando o conteúdo

| Quero…                         | Onde mexer                                         |
| ------------------------------ | -------------------------------------------------- |
| Mudar bio, links ou contatos   | `perfil` em `data.json` e `data.en.json`           |
| Adicionar uma experiência      | `trajetoria`                                       |
| Adicionar um projeto           | `projetos`                                         |
| Trocar o currículo             | substituir `assets/docs/curriculo-rafael-inacio.pdf` |
| Mudar título/descrição da aba  | `textos.meta.paginas`                              |
| Mudar cores ou fontes          | tokens no início de `style.css`                    |
| Reordenar seções               | `PortfolioApp.PAGES` em `js/app/PortfolioApp.js`   |
