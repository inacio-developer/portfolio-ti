import { createElement } from '../core/dom.js';

/**
 * ThemeSwitcher — botão para alternar entre o modo claro e o escuro.
 *
 * Como funciona:
 *   - sem escolha da pessoa, o site segue o tema do sistema (CSS prefers-color-scheme);
 *   - ao clicar, grava a escolha em <html data-theme="light|dark">, que vence o sistema
 *     (ver os blocos de tema no início do style.css);
 *   - a escolha fica salva no navegador e é reaplicada antes da página aparecer
 *     (script curtinho no <head> dos HTML), para não piscar o tema errado.
 */

/** Onde a escolha fica salva. O mesmo nome é usado no script do <head> dos HTML. */
export const THEME_STORAGE_KEY = 'portfolio:tema';

const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)');

export class ThemeSwitcher {
  #labels;
  #button = null;

  /**
   * @param {object} labels  textos.tema do data.json
   * @param {string} labels.paraEscuro  Texto do botão quando o site está claro.
   * @param {string} labels.paraClaro   Texto do botão quando o site está escuro.
   */
  constructor(labels = {}) {
    this.#labels = labels;
  }

  /** Coloca o botão dentro do elemento indicado (o menu do topo). */
  mountInto(container) {
    if (!container || !this.#labels.paraEscuro || !this.#labels.paraClaro) return;

    this.#button = createElement(
      'button',
      { type: 'button', class: 'theme-switch', onClick: () => this.toggle() },
      createElement('span', { class: 'theme-switch__icon', 'aria-hidden': 'true' })
    );
    container.append(this.#button);
    this.#updateButtonLabel();
    ThemeSwitcher.#syncBrowserBarColor();

    // Se a pessoa nunca escolheu e o sistema mudar de tema, o rótulo acompanha.
    systemPrefersDark.addEventListener('change', () => this.#updateButtonLabel());
  }

  /** Tema que está valendo agora: o escolhido no botão ou, sem escolha, o do sistema. */
  get currentTheme() {
    const chosenTheme = document.documentElement.dataset.theme;
    if (chosenTheme === 'light' || chosenTheme === 'dark') return chosenTheme;
    return systemPrefersDark.matches ? 'dark' : 'light';
  }

  toggle() {
    const nextTheme = this.currentTheme === 'dark' ? 'light' : 'dark';
    const applyTheme = () => {
      document.documentElement.dataset.theme = nextTheme;
      this.#updateButtonLabel();
      ThemeSwitcher.#syncBrowserBarColor();
    };

    // Transição suave entre os temas onde o navegador suporta (e se a pessoa não
    // pediu menos movimento); nos outros, a troca é instantânea.
    const prefersLessMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (document.startViewTransition && !prefersLessMotion) {
      document.startViewTransition(applyTheme);
    } else {
      applyTheme();
    }

    ThemeSwitcher.#saveChoice(nextTheme);
  }

  /** O botão descreve o que vai acontecer ao clicar ("Mudar para o modo escuro"). */
  #updateButtonLabel() {
    if (!this.#button) return;
    const label = this.currentTheme === 'dark' ? this.#labels.paraClaro : this.#labels.paraEscuro;
    this.#button.setAttribute('aria-label', label);
    this.#button.title = label;
  }

  /**
   * No celular, a barra do navegador usa a cor de <meta name="theme-color">.
   * Os HTML trazem uma cor para cada tema do sistema; quando a pessoa escolhe
   * um tema no botão, as duas passam a usar a cor de fundo do tema escolhido.
   */
  static #syncBrowserBarColor() {
    if (!document.documentElement.dataset.theme) return;
    const backgroundColor = getComputedStyle(document.documentElement).getPropertyValue('--bg').trim();
    document.querySelectorAll('meta[name="theme-color"]').forEach((meta) => meta.setAttribute('content', backgroundColor));
  }

  static #saveChoice(theme) {
    try {
      localStorage.setItem(THEME_STORAGE_KEY, theme);
    } catch {
      // Armazenamento bloqueado (ex.: janela anônima restrita): vale só nesta visita.
    }
  }
}
