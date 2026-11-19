import { createElement } from '../core/dom.js';
import { Component } from './Component.js';

/**
 * Section — base das seções editoriais dentro do <main>.
 *
 * Cuida da parte repetitiva de toda seção:
 *   - a tag <section> com id e o título pequeno (h2);
 *   - a ligação entre título e seção para leitores de tela (aria-labelledby);
 *   - a regra de resiliência: se content() não devolver nada, a seção não aparece.
 *
 * Cada subclasse só precisa definir:
 *   static id   → id da âncora na página (#sobre, #projetos…)
 *   get title() → título da seção, vindo de data.textos
 *   content()   → elementos do corpo da seção ([] para esconder a seção)
 */
export class Section extends Component {
  static id = '';

  get id() {
    return this.constructor.id;
  }

  get title() {
    return '';
  }

  /** @returns {Array<Node|null>} */
  content() {
    return [];
  }

  /** Separador de listas na mesma linha (" · "), usado por várias seções. */
  get listSeparator() {
    return this.uiText('rotulos.separadorLista', ' · ');
  }

  render() {
    const bodyElements = [this.content()].flat(Infinity).filter(Boolean);
    const hasContent = bodyElements.length > 0;
    if (!hasContent) return null;

    const titleId = `${this.id}-titulo`;

    return createElement(
      'section',
      { class: 'section', id: this.id, 'aria-labelledby': titleId },
      createElement('h2', { class: 'section__title', id: titleId }, this.title),
      bodyElements
    );
  }
}
