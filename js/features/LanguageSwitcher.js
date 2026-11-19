import { createElement } from '../core/dom.js';

/**
 * LanguageSwitcher — escolhe o idioma do site e mostra o botão "EN" / "PT" no menu.
 *
 * Cada idioma tem o seu arquivo de dados com a mesma estrutura
 * (data.json em português, data.en.json em inglês; ver main.js).
 *
 * Qual idioma vale, em ordem de prioridade:
 *   1. ?lang=en no endereço (bom para mandar o link já em inglês);
 *   2. a escolha feita no botão, salva no navegador;
 *   3. o idioma do navegador: português para quem usa português, inglês para o resto.
 *
 * O botão em si vem de textos.idioma em cada arquivo de dados:
 *   { "alvo": "en", "rotulo": "EN", "descricao": "Read in English" }
 */

/** Onde a escolha fica salva no navegador. */
export const LANGUAGE_STORAGE_KEY = 'portfolio:idioma';

/** Parâmetro do endereço que força um idioma (?lang=en). */
const URL_PARAMETER = 'lang';

export class LanguageSwitcher {
  #target;

  /** @param {{alvo: string, rotulo: string, descricao: string}} labels  textos.idioma */
  constructor(labels = {}) {
    this.#target = labels;
  }

  /**
   * Decide o idioma desta visita.
   * @param {string[]} supportedLanguages  ex.: ['pt', 'en']
   * @param {string}   defaultLanguage     usado se nada mais servir
   */
  static resolve(supportedLanguages, defaultLanguage) {
    const isSupported = (language) => supportedLanguages.includes(language);

    const fromAddress = new URLSearchParams(location.search).get(URL_PARAMETER);
    if (isSupported(fromAddress)) {
      // Guarda, para o idioma continuar ao navegar entre as páginas.
      LanguageSwitcher.#saveChoice(fromAddress);
      return fromAddress;
    }

    const savedChoice = LanguageSwitcher.#readChoice();
    if (isSupported(savedChoice)) return savedChoice;

    const browserLanguages = navigator.languages?.length ? navigator.languages : [navigator.language ?? ''];
    const browserSpeaksPortuguese = browserLanguages.some((language) => language.toLowerCase().startsWith('pt'));
    const browserLanguage = browserSpeaksPortuguese ? 'pt' : 'en';
    return isSupported(browserLanguage) ? browserLanguage : defaultLanguage;
  }

  /** Coloca o botão dentro do elemento indicado (o menu do topo). */
  mountInto(container) {
    const { alvo: targetLanguage, rotulo: label, descricao: description } = this.#target;
    if (!container || !targetLanguage || !label) return;

    const button = createElement(
      'button',
      {
        type: 'button',
        class: 'language-switch',
        lang: targetLanguage,
        'aria-label': description || label,
        title: description || null,
        onClick: () => LanguageSwitcher.#switchTo(targetLanguage),
      },
      label
    );
    container.append(button);
  }

  /** Salva a escolha e recarrega a página já no outro idioma. */
  static #switchTo(language) {
    LanguageSwitcher.#saveChoice(language);

    const address = new URL(location.href);
    // Se o endereço força um idioma, ele venceria a escolha: atualiza também.
    if (address.searchParams.has(URL_PARAMETER)) address.searchParams.set(URL_PARAMETER, language);
    location.replace(address);
  }

  static #readChoice() {
    try {
      return localStorage.getItem(LANGUAGE_STORAGE_KEY);
    } catch {
      return null;
    }
  }

  static #saveChoice(language) {
    try {
      localStorage.setItem(LANGUAGE_STORAGE_KEY, language);
    } catch {
      // Armazenamento bloqueado: o idioma vale só nesta página.
    }
  }
}
