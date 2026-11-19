import { toElementList } from '../core/dom.js';
import { asArray, readPath } from '../core/utils.js';
import { Curiosities } from '../features/Curiosities.js';
import { EdgeScrollNavigation } from '../features/EdgeScrollNavigation.js';
import { LanguageSwitcher } from '../features/LanguageSwitcher.js';
import { ThemeSwitcher } from '../features/ThemeSwitcher.js';
import { MediumService } from '../services/MediumService.js';
import { PortfolioService } from '../services/PortfolioService.js';
import { Announcer } from '../ui/Announcer.js';
import { MetaManager } from './MetaManager.js';

import { Nav } from '../components/Nav.js';
import { Hero } from '../components/Hero.js';
import { About } from '../components/About.js';
import { Projects } from '../components/Projects.js';
import { WritingsArchive } from '../components/Writings.js';
import { WritingsHeader } from '../components/WritingsHeader.js';
import { Timeline } from '../components/Timeline.js';
import { Skills } from '../components/Skills.js';
import { Contact } from '../components/Contact.js';
import { Footer } from '../components/Footer.js';

/**
 * PortfolioApp — o maestro do site.
 *
 * Passo a passo:
 *   1. Carrega o data.json (PortfolioService) e aplica título/descrição (MetaManager).
 *   2. Monta a página atual com os componentes listados em PAGES.
 *   3. Em segundo plano, busca os artigos do Medium (MediumService). Quando
 *      chegam, redesenha só as seções marcadas com `static updatesWithMedium = true`.
 *   4. Liga as curiosidades: desenhos pessoais que surgem nas margens (Curiosities).
 *   5. Liga a troca de página ao rolar além da borda (EdgeScrollNavigation).
 *
 * Para criar uma página: adicione uma entrada em PAGES e um HTML com <body data-pagina="chave">.
 * Para reordenar ou esconder seções: edite a lista `sections` da página.
 *
 * `scrollPastEdge` (opcional) diz para onde ir ao rolar além do fim/topo:
 *   direction   → 'down' (passou do fim) ou 'up' (passou do topo)
 *   toPage      → chave da página de destino (o endereço vem de textos.navegacao)
 *   messagePath → texto do aviso, em data.textos
 *   arriveAtBottom → abrir o destino já no fim (para quem "sobe" de volta)
 */
export class PortfolioApp {
  static PAGES = {
    inicio: {
      header: Hero,
      sections: [About, Projects, Timeline, Skills, Contact],
      scrollPastEdge: {
        direction: 'down',
        toPage: 'escritos',
        messagePath: 'navegacaoPorRolagem.paraEscritos',
      },
    },
    escritos: {
      header: WritingsHeader,
      sections: [WritingsArchive],
      scrollPastEdge: {
        direction: 'up',
        toPage: 'inicio',
        messagePath: 'navegacaoPorRolagem.paraInicio',
        arriveAtBottom: true,
      },
    },
  };

  /**
   * Um arquivo de dados por idioma, com a mesma estrutura.
   * Para mudar um texto, edite os dois arquivos.
   * O idioma da visita é escolhido pelo LanguageSwitcher (endereço, botão ou navegador).
   */
  static DATA_FILE_BY_LANGUAGE = {
    pt: 'data.json',
    en: 'data.en.json',
  };

  static DEFAULT_LANGUAGE = 'pt';

  #portfolioService;
  #metaManager = new MetaManager();
  #currentPage;
  #sharedServices;
  #pageAreas;
  #data = null;

  /** Guarda o elemento que cada seção desenhou, para poder trocá-lo depois. */
  #renderedSections = new Map();

  /**
   * @param {object} [options]
   * @param {string} [options.page]     Chave em PAGES (vem de <body data-pagina>).
   */
  constructor({ page = 'inicio' } = {}) {
    const dataFiles = PortfolioApp.DATA_FILE_BY_LANGUAGE;
    const language = LanguageSwitcher.resolve(Object.keys(dataFiles), PortfolioApp.DEFAULT_LANGUAGE);
    this.#portfolioService = new PortfolioService(dataFiles[language]);
    this.#currentPage = PortfolioApp.PAGES[page] ? page : 'inicio';

    // Entregue a todos os componentes (ficam em this.services dentro deles).
    this.#sharedServices = {
      announcer: new Announcer('#anuncio'),
      currentPage: this.#currentPage,
    };

    // Lugares do HTML onde cada parte da página é montada.
    this.#pageAreas = {
      nav: document.getElementById('navegacao'),
      header: document.getElementById('hero'),
      main: document.getElementById('conteudo'),
      footer: document.getElementById('rodape'),
    };
  }

  /** Componentes da página atual (um item de PAGES). */
  get #pageLayout() {
    return PortfolioApp.PAGES[this.#currentPage];
  }

  async init() {
    try {
      this.#data = await this.#portfolioService.load();
      this.#metaManager.apply(this.#data, this.#currentPage);
      this.#renderPage();
      this.#setPageState('ready');
    } catch (error) {
      // Sem data.json não há texto para mostrar: o cursor do loader para,
      // fica vazado (CSS .is-error) e o detalhe vai para o console.
      console.error('[portfólio] Falha ao carregar os dados:', error);
      this.#setPageState('error');
      return;
    } finally {
      this.#pageAreas.main.removeAttribute('aria-busy');
    }

    // Não espera o Medium: os artigos do data.json aparecem já, os do Medium logo depois.
    this.#updateArticlesFromMedium();

    // Desenhos pessoais que surgem nas margens de tempos em tempos.
    new Curiosities(this.#data.curiosidades).start();

    // Rolar além do fim/topo leva para a outra página.
    this.#startScrollPastEdgeNavigation();
  }

  /* ------------------------------------------------------------------ */
  /* Navegação por rolagem                                               */
  /* ------------------------------------------------------------------ */

  async #startScrollPastEdgeNavigation() {
    // Quem chegou "subindo" da página de Escritos abre no fim desta página.
    // Espera as fontes carregarem, porque elas mudam a altura da página.
    await document.fonts?.ready;
    EdgeScrollNavigation.restoreArrivalPosition();

    const settings = this.#pageLayout.scrollPastEdge;
    if (!settings) return;

    const message = readPath(this.#data.textos, settings.messagePath);
    const targetUrl = this.#addressOfPage(settings.toPage);
    if (!message || !targetUrl) return;

    new EdgeScrollNavigation({
      direction: settings.direction,
      targetUrl,
      message,
      arriveAtBottom: settings.arriveAtBottom,
    }).start();
  }

  /** Endereço de uma página, procurado no menu (textos.navegacao). */
  #addressOfPage(pageKey) {
    const menuItems = asArray(readPath(this.#data.textos, 'navegacao', []));
    return menuItems.find((item) => item.pagina === pageKey)?.href ?? '';
  }

  /* ------------------------------------------------------------------ */
  /* Montagem da página                                                  */
  /* ------------------------------------------------------------------ */

  /** Cria o componente com os dados e serviços e devolve o que ele desenhou. */
  #renderComponent(ComponentClass) {
    const component = new ComponentClass(this.#data, this.#sharedServices);
    return component.render();
  }

  #renderPage() {
    const { nav, header, footer } = this.#pageAreas;

    nav?.replaceChildren(...toElementList(this.#renderComponent(Nav)));
    new LanguageSwitcher(readPath(this.#data.textos, 'idioma', {})).mountInto(nav);
    new ThemeSwitcher(readPath(this.#data.textos, 'tema', {})).mountInto(nav);
    header.replaceChildren(...toElementList(this.#renderComponent(this.#pageLayout.header)));
    this.#renderSections();
    footer.replaceChildren(...toElementList(this.#renderComponent(Footer)));

    this.#numberBlocksForEntranceAnimation();
  }

  #renderSections() {
    this.#renderedSections.clear();

    for (const SectionClass of this.#pageLayout.sections) {
      const [sectionElement = null] = toElementList(this.#renderComponent(SectionClass));
      this.#renderedSections.set(SectionClass, sectionElement);
    }

    const visibleSections = [...this.#renderedSections.values()].filter(Boolean);
    this.#pageAreas.main.replaceChildren(...visibleSections);
  }

  /* ------------------------------------------------------------------ */
  /* Atualização com o Medium                                            */
  /* ------------------------------------------------------------------ */

  /** Busca o Medium, junta com os artigos do data.json e redesenha as seções de artigos. */
  async #updateArticlesFromMedium() {
    const { fonte: mediumSettings, itens: savedArticles } = this.#data.escritos;
    const sectionsToUpdate = this.#pageLayout.sections.filter((SectionClass) => SectionClass.updatesWithMedium);
    if (!mediumSettings || sectionsToUpdate.length === 0) return;

    try {
      const mediumArticles = await new MediumService(mediumSettings).fetchArticles();
      this.#data.escritos.itens = MediumService.mergeWithSaved(mediumArticles, savedArticles);
    } catch (error) {
      console.warn('[portfólio] Medium indisponível, mantendo os artigos do data.json.', error);
      return;
    }

    for (const SectionClass of sectionsToUpdate) this.#redrawSection(SectionClass);
  }

  /** Troca o elemento de uma seção pelo desenho novo, sem repetir a animação de entrada. */
  #redrawSection(SectionClass) {
    const oldElement = this.#renderedSections.get(SectionClass);
    const [newElement = null] = toElementList(this.#renderComponent(SectionClass));
    newElement?.classList.add('no-enter');

    if (oldElement && newElement) {
      oldElement.replaceWith(newElement);
    } else if (oldElement) {
      oldElement.remove();
    } else if (newElement) {
      // A seção não existia antes (data.json sem artigos): insere no lugar certo.
      this.#pageAreas.main.insertBefore(newElement, this.#nextVisibleSectionAfter(SectionClass));
    }

    this.#renderedSections.set(SectionClass, newElement);
  }

  /** Primeira seção já visível que vem depois desta na ordem da página (ou null = fim). */
  #nextVisibleSectionAfter(SectionClass) {
    const sectionOrder = this.#pageLayout.sections;
    const sectionsAfter = sectionOrder.slice(sectionOrder.indexOf(SectionClass) + 1);
    return sectionsAfter.map((Later) => this.#renderedSections.get(Later)).find(Boolean) ?? null;
  }

  /* ------------------------------------------------------------------ */
  /* Estado visual                                                       */
  /* ------------------------------------------------------------------ */

  /** Dá a cada bloco um número de ordem; o CSS usa --i para escalonar a entrada. */
  #numberBlocksForEntranceAnimation() {
    document
      .querySelectorAll('.site-nav, .hero > *, main > .section, .footer')
      .forEach((block, position) => block.style.setProperty('--i', position));
  }

  /** Troca a classe do <body>: is-loading → is-ready ou is-error. */
  #setPageState(state) {
    document.body.classList.remove('is-loading');
    document.body.classList.add(`is-${state}`);
  }
}
