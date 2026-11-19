/**
 * Portfólio — Rafael Inácio
 * Ponto de entrada. Carregado como módulo ES por index.html e escritos.html.
 *
 * Arquitetura data-driven: nenhum texto de conteúdo vive no código.
 * Tudo vem de data.json (perfil, trajetoria, projetos, escritos, textos);
 * os escritos ainda são atualizados ao vivo pelo feed do Medium.
 * A versão em inglês usa data.en.json, com a mesma estrutura.
 *
 *   js/
 *   ├── main.js                → este arquivo
 *   ├── app/                   → orquestração (PortfolioApp, MetaManager)
 *   ├── services/              → dados e APIs (data.json, Medium, clipboard)
 *   ├── components/            → uma classe por bloco da página
 *   ├── features/              → comportamentos fora das seções (curiosidades nas margens)
 *   ├── ui/                    → peças reutilizáveis (Link, Announcer)
 *   └── core/                  → funções puras (dom, utils)
 */
import { PortfolioApp } from './app/PortfolioApp.js';

const page = document.body.dataset.pagina;

// O idioma (e qual arquivo de dados carregar) é decidido dentro do PortfolioApp.
new PortfolioApp({ page }).init();
