import { createElement } from '../core/dom.js';
import { Component } from './Component.js';

/**
 * WritingsHeader — topo da página de escritos (faz o papel do Hero nessa página).
 * Usa as mesmas classes do Hero, inclusive o cursor de redação (assinatura #1).
 */
export class WritingsHeader extends Component {
  render() {
    const { titulo: title, introducao: introduction } = this.uiText('paginaEscritos', {});
    if (!title) return null;

    const blinkingCursor = createElement('span', { class: 'caret', 'aria-hidden': 'true' });

    return [
      createElement('h1', { class: 'hero__name' }, title, blinkingCursor),
      introduction ? createElement('p', { class: 'hero__lede' }, introduction) : null,
    ];
  }
}
